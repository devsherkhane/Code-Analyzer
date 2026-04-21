package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// -----------------------------------------------------------------------------
// TYPES & CONSTANTS
// -----------------------------------------------------------------------------

type JobPayload struct {
	FilePath string
}

type InternalJob struct {
	ID      string
	Payload JobPayload
}

const (
	StatusQueued  = "queued"
	StatusRunning = "running"
	StatusDone    = "done"
	StatusError   = "error"
)

// -----------------------------------------------------------------------------
// GLOBAL STATE
// -----------------------------------------------------------------------------

var (
	jobs = make(map[string]struct {
		Status   string
		ErrorMsg string
	})
	jobsMu   sync.RWMutex
	jobQueue = make(chan InternalJob, 100)
)

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

// -----------------------------------------------------------------------------
// INTERNAL WORKER LOGIC
// -----------------------------------------------------------------------------

func startInternalWorkers(concurrency int) {
	for i := 0; i < concurrency; i++ {
		go func(workerID int) {
			fmt.Printf("[WORKER %d] Started\n", workerID)
			for job := range jobQueue {
				processJob(job)
			}
		}(i)
	}
}

func processJob(job InternalJob) {
	jobID := job.ID
	payload := job.Payload

	// Update status to Running
	jobsMu.Lock()
	jobs[jobID] = struct{ Status, ErrorMsg string }{Status: StatusRunning, ErrorMsg: ""}
	jobsMu.Unlock()

	fmt.Printf("[JOB %s] Analysis started for: %s\n", jobID, payload.FilePath)

	// Setup log file for SSE tailing
	logPath := filepath.Join(".", "logs", fmt.Sprintf("job-%s.log", jobID))
	logFile, err := os.Create(logPath)
	if err != nil {
		updateJobStatus(jobID, StatusError, fmt.Sprintf("failed to create log file: %v", err))
		return
	}
	defer logFile.Close()

	// 30-minute timeout for analysis
	execCtx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
	defer cancel()

	// Determine python command (handle Windows/Unix differences)
	pythonCmd := "python"
	if _, err := exec.LookPath("python3"); err == nil {
		pythonCmd = "python3"
	}

	// Convert upload path to an absolute path so the analyzer can find it
	absFilePath, _ := filepath.Abs(payload.FilePath)

	cmd := exec.CommandContext(execCtx, pythonCmd, "main.py", absFilePath)
	// Run Python from the analyzer/ directory so all relative imports work
	cmd.Dir = filepath.Join("..", "analyzer")
	
	stdout, _ := cmd.StdoutPipe()
	stderr, _ := cmd.StderrPipe()
	
	if err := cmd.Start(); err != nil {
		updateJobStatus(jobID, StatusError, fmt.Sprintf("failed to start python analyzer: %v", err))
		logFile.WriteString(fmt.Sprintf("[ERROR] %v\n", err))
		return
	}

	// Stream Python logs directly to the job's log file using WaitGroup for clean finish
	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
			logFile.WriteString(scanner.Text() + "\n")
			logFile.Sync()
		}
	}()
	
	go func() {
		defer wg.Done()
		scanner := bufio.NewScanner(stderr)
		for scanner.Scan() {
			logFile.WriteString("[ERROR] " + scanner.Text() + "\n")
			logFile.Sync()
		}
	}()

	err = cmd.Wait()
	wg.Wait() // Ensure all logs are written
	
	jobsMu.Lock()
	if err != nil {
		if execCtx.Err() == context.DeadlineExceeded {
			jobs[jobID] = struct{ Status, ErrorMsg string }{Status: StatusError, ErrorMsg: "Analysis timed out after 30 minutes"}
		} else {
			jobs[jobID] = struct{ Status, ErrorMsg string }{Status: StatusError, ErrorMsg: fmt.Sprintf("Analysis failed: %v", err)}
		}
		fmt.Printf("[JOB %s] Failed: %v\n", jobID, err)
	} else {
		jobs[jobID] = struct{ Status, ErrorMsg string }{Status: StatusDone, ErrorMsg: ""}
		fmt.Printf("[JOB %s] Completed successfully\n", jobID)
	}
	jobsMu.Unlock()
}

func updateJobStatus(id, status, errMsg string) {
	jobsMu.Lock()
	defer jobsMu.Unlock()
	jobs[id] = struct{ Status, ErrorMsg string }{Status: status, ErrorMsg: errMsg}
}

// -----------------------------------------------------------------------------
// GIN HTTP SERVER
// -----------------------------------------------------------------------------

func main() {
	// Initialize directories
	os.MkdirAll("./uploads", 0755)
	os.MkdirAll("./logs", 0755)
	os.MkdirAll("./json_reports", 0755)

	// Auto-start Flask analysis server for VS Code extension + /api/analyze-uiux
	go func() {
		pythonCmd := "python"
		if _, err := exec.LookPath("python3"); err == nil {
			pythonCmd = "python3"
		}
		flask := exec.Command(pythonCmd, "analysis_server.py")
		flask.Dir = filepath.Join("..", "analyzer")
		flask.Stdout = os.Stdout
		flask.Stderr = os.Stderr
		fmt.Println("[SERVER] Starting Flask analysis bridge on :7891")
		if err := flask.Run(); err != nil {
			fmt.Printf("[SERVER] Flask bridge failed to start: %v (non-fatal)\n", err)
		}
	}()

	// Start Internal Workers (No Redis required)
	startInternalWorkers(5)

	r := gin.Default()

	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*") // Development mode
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// 1. STANDARD ZIP UPLOAD
	r.POST("/upload", func(c *gin.Context) {
		file, err := c.FormFile("file")
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "No file uploaded"})
			return
		}

		path := filepath.Join("./uploads", file.Filename)
		if err := c.SaveUploadedFile(file, path); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save file"})
			return
		}

		// Create unique job ID
		jobID := uuid.New().String()

		// Store status
		jobsMu.Lock()
		jobs[jobID] = struct{ Status, ErrorMsg string }{Status: StatusQueued, ErrorMsg: ""}
		jobsMu.Unlock()

		// Enqueue to internal channel
		jobQueue <- InternalJob{
			ID:      jobID,
			Payload: JobPayload{FilePath: path},
		}

		c.JSON(200, gin.H{
			"msg":    "File uploaded, analysis queued internally (No Redis).",
			"job_id": jobID,
		})
	})

	// 2. GITHUB WEBHOOK INGESTION
	r.POST("/webhook/github", func(c *gin.Context) {
		var payload struct {
			Action      string `json:"action"`
			PullRequest struct {
				Head struct {
					Ref string `json:"ref"`
					Repo struct {
						Name     string `json:"name"`
						FullName string `json:"full_name"`
					} `json:"repo"`
				} `json:"head"`
			} `json:"pull_request"`
		}

		if err := c.BindJSON(&payload); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid webhook payload"})
			return
		}

		if payload.Action != "opened" && payload.Action != "synchronize" {
			c.JSON(200, gin.H{"msg": "Ignored action type"})
			return
		}

		repoName := payload.PullRequest.Head.Repo.Name
		branch := payload.PullRequest.Head.Ref
		targetZipPath := filepath.Join(".", "uploads", fmt.Sprintf("%s-%s.zip", repoName, branch))

		jobID := uuid.New().String()

		jobsMu.Lock()
		jobs[jobID] = struct{ Status, ErrorMsg string }{Status: StatusQueued, ErrorMsg: ""}
		jobsMu.Unlock()

		jobQueue <- InternalJob{
			ID:      jobID,
			Payload: JobPayload{FilePath: targetZipPath},
		}

		c.JSON(200, gin.H{"msg": "Webhook received, PR enqueued internally.", "job_id": jobID})
	})

	// 3. ANALYSIS HISTORY API
	r.GET("/api/history", func(c *gin.Context) {
		files, err := filepath.Glob("./json_reports/ai_report_*.json")
		if err != nil {
			c.JSON(500, gin.H{"error": "Failed to scan reports"})
			return
		}

		type ReportSummary struct {
			ReportID     string  `json:"report_id"`
			ProjectName  string  `json:"project_name"`
			OverallScore float64 `json:"overall_score"`
			TotalIssues  int     `json:"total_issues"`
			Timestamp    string  `json:"timestamp"`
		}

		var history []ReportSummary
		for _, f := range files {
			data, err := os.ReadFile(f)
			if err != nil {
				continue
			}
			var report struct {
				ReportID     string  `json:"report_id"`
				ProjectName  string  `json:"project_name"`
				OverallScore float64 `json:"overall_score"`
				TotalIssues  int     `json:"total_issues"`
				Timestamp    string  `json:"timestamp"`
			}
			if err := json.Unmarshal(data, &report); err == nil {
				history = append(history, ReportSummary{
					ReportID:     report.ReportID,
					ProjectName:  report.ProjectName,
					OverallScore: report.OverallScore,
					TotalIssues:  report.TotalIssues,
					Timestamp:    report.Timestamp,
				})
			}
		}

		c.JSON(200, history)
	})

	r.POST("/api/analyze-workspace", func(c *gin.Context) {
		var payload struct {
			Path string `json:"path"`
		}
		if err := c.BindJSON(&payload); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid payload"})
			return
		}

		if _, err := os.Stat(payload.Path); os.IsNotExist(err) {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Directory does not exist"})
			return
		}

		jobID := uuid.New().String()
		jobsMu.Lock()
		jobs[jobID] = struct{ Status, ErrorMsg string }{Status: StatusQueued, ErrorMsg: ""}
		jobsMu.Unlock()

		jobQueue <- InternalJob{
			ID: jobID,
			Payload: JobPayload{
				FilePath: payload.Path,
			},
		}

		c.JSON(200, gin.H{
			"job_id": jobID,
			"msg":    fmt.Sprintf("Direct analysis started for: %s", payload.Path),
		})
	})

	r.GET("/status/:id", func(c *gin.Context) {
		jobID := c.Param("id")
		jobsMu.RLock()
		job, exists := jobs[jobID]
		jobsMu.RUnlock()

		if !exists {
			c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
			return
		}

		c.JSON(200, gin.H{
			"status":    job.Status,
			"error_msg": job.ErrorMsg,
		})
	})

	r.GET("/progress/:id", func(c *gin.Context) {
		jobID := c.Param("id")
		logPath := filepath.Join(".", "logs", fmt.Sprintf("job-%s.log", jobID))

		// SSE Headers
		c.Writer.Header().Set("Content-Type", "text/event-stream")
		c.Writer.Header().Set("Cache-Control", "no-cache")
		c.Writer.Header().Set("Connection", "keep-alive")
		c.Writer.Header().Set("Transfer-Encoding", "chunked")

		file, err := os.Open(logPath)
		if err != nil {
			fmt.Fprintf(c.Writer, "data: Waiting for log file creation...\n\n")
			c.Writer.Flush()
			
			for i := 0; i < 15; i++ {
				time.Sleep(1 * time.Second)
				file, err = os.Open(logPath)
				if err == nil {
					break
				}
			}
			if err != nil {
				return
			}
		}
		defer file.Close()

		reader := bufio.NewReader(file)
		watcherCtx, cancel := context.WithCancel(c.Request.Context())
		defer cancel()

		for {
			select {
			case <-watcherCtx.Done():
				return
			default:
				line, err := reader.ReadString('\n')
				if err != nil {
					if err == io.EOF {
						time.Sleep(500 * time.Millisecond)
						
						jobsMu.RLock()
						status := jobs[jobID].Status
						jobsMu.RUnlock()
						
						if status == StatusDone || status == StatusError {
							c.SSEvent("message", "--- ANALYSIS FINISHED ---")
							return
						}
						continue
					}
					return
				}
				c.SSEvent("message", line)
				c.Writer.Flush()
			}
		}
	})

	r.GET("/file-content", func(c *gin.Context) {
		filePath := c.Query("path")
		if filePath == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Path is required"})
			return
		}

		// Security: Prevent directory traversal — reject absolute paths
		cleanPath := filepath.Clean(filePath)

		// Try multiple locations since the Python analyzer can run from
		// either backend/ or analyzer/ CWD depending on the setup
		candidates := []string{
			filepath.Join(".", cleanPath),                      // backend/<path>
			filepath.Join("..", "analyzer", cleanPath),          // analyzer/<path>
		}

		// If the path is absolute, try it directly (the analyzer may store abs paths)
		if filepath.IsAbs(cleanPath) {
			candidates = append([]string{cleanPath}, candidates...)
		}

		var fullPath string
		for _, cp := range candidates {
			if _, err := os.Stat(cp); err == nil {
				fullPath = cp
				break
			}
		}

		fmt.Printf("[DEBUG] Fetching file: query=%s resolved=%s\n", filePath, fullPath)

		if fullPath == "" {
			c.JSON(http.StatusNotFound, gin.H{"error": "File not found on disk"})
			return
		}

		content, err := os.ReadFile(fullPath)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to read file: %v", err)})
			return
		}

		c.String(200, string(content))
	})

	r.POST("/api/analyze-uiux", func(c *gin.Context) {
		var payload struct {
			FilePath string `json:"file_path"`
			Content  string `json:"content"`
		}
		if err := c.BindJSON(&payload); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid payload"})
			return
		}

		reqData, _ := json.Marshal(payload)
		resp, err := http.Post("http://127.0.0.1:7891/analyze-file", "application/json", bytes.NewBuffer(reqData))
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Flask analysis server is not running"})
			return
		}
		defer resp.Body.Close()

		body, _ := io.ReadAll(resp.Body)
		c.Data(resp.StatusCode, "application/json", body)
	})

	r.StaticFile("/ai_architecture", "./ai_architecture.json")
	r.StaticFile("/ai_report", "./ai_report.json")
	r.StaticFile("/dependency_graph", "./json_reports/dependency_graph.json")

	r.StaticFS("/assets", http.Dir("./dist/assets"))
	r.StaticFile("/favicon.ico", "./dist/favicon.ico")
	r.NoRoute(func(c *gin.Context) {
		c.File("./dist/index.html")
	})

	fmt.Println("[SERVER] Listening on :8081 (Internal Worker Mode)")
	r.Run(":8081")
}
