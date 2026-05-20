package main

import (
	"bufio"
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
)

type Job struct {
	ID       string        `json:"job_id"`
	Status   string        `json:"status"` // "queued", "running", "done", "error"
	ErrorMsg string        `json:"error,omitempty"`
	Logs     []string      `json:"-"`
	Clients  []chan string `json:"-"`
	Mutex    sync.Mutex    `json:"-"`
}

var (
	jobs      = make(map[string]*Job)
	jobsMutex sync.RWMutex
)

func updateJobStatus(jobID, status, errMsg string) {
	jobsMutex.Lock()
	defer jobsMutex.Unlock()
	if job, exists := jobs[jobID]; exists {
		job.Mutex.Lock()
		job.Status = status
		job.ErrorMsg = errMsg
		job.Mutex.Unlock()
	}
}

func appendJobLog(jobID, line string) {
	jobsMutex.RLock()
	job, exists := jobs[jobID]
	jobsMutex.RUnlock()

	if exists {
		job.Mutex.Lock()
		job.Logs = append(job.Logs, line)
		// Send to all connected SSE clients
		for _, ch := range job.Clients {
			select {
			case ch <- line:
			default:
			}
		}
		job.Mutex.Unlock()
	}
}

func runAnalysisJob(jobID string, path string) {
	updateJobStatus(jobID, "running", "")

	cmd := exec.Command("python", "../analyzer/main.py", path)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		updateJobStatus(jobID, "error", fmt.Sprintf("Failed to redirect stdout: %v", err))
		return
	}
	cmd.Stderr = cmd.Stdout // Capture stderr too

	if err := cmd.Start(); err != nil {
		updateJobStatus(jobID, "error", fmt.Sprintf("Failed to start analysis process: %v", err))
		return
	}

	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		appendJobLog(jobID, line)
	}

	if err := cmd.Wait(); err != nil {
		updateJobStatus(jobID, "error", fmt.Sprintf("Analysis failed with exit code: %v", err))
		return
	}

	updateJobStatus(jobID, "done", "")
}

type HistoryReport struct {
	ReportID     string `json:"report_id"`
	ProjectName  string `json:"project_name"`
	OverallScore int    `json:"overall_score"`
	TotalIssues  int    `json:"total_issues"`
	Timestamp    string `json:"timestamp"`
}

func main() {
	r := gin.Default()

	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	if _, err := os.Stat("./uploads"); os.IsNotExist(err) {
		os.Mkdir("./uploads", 0755)
	}

	// ── Serve Static Frontend Dashboard Assets ───────────────────
	r.Static("/assets", "./dist/assets")
	r.StaticFile("/vite.svg", "./dist/vite.svg")

	// ── REST API Endpoints ────────────────────────────────────────

	r.GET("/file-content", func(c *gin.Context) {
		filePath := c.Query("path")
		if filePath == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "path parameter is required"})
			return
		}

		data, err := os.ReadFile(filePath)
		if err != nil {
			data, err = os.ReadFile("../" + filePath)
			if err != nil {
				cleaned := filepath.Clean(filePath)
				data, err = os.ReadFile(cleaned)
				if err != nil {
					data, err = os.ReadFile("../" + cleaned)
					if err != nil {
						c.JSON(http.StatusNotFound, gin.H{"error": "file not found: " + err.Error()})
						return
					}
				}
			}
		}

		c.String(http.StatusOK, string(data))
	})

	r.POST("/upload", func(c *gin.Context) {
		file, err := c.FormFile("file")
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "No file uploaded"})
			return
		}

		path := "./uploads/" + file.Filename
		if err := c.SaveUploadedFile(file, path); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save file"})
			return
		}

		cmd := exec.Command("python", "../analyzer/main.py", path)
		output, err := cmd.CombinedOutput()
		if err != nil {
			fmt.Printf("Python Traceback: %s\n", string(output))
			c.JSON(http.StatusInternalServerError, gin.H{"msg": "Python script failed", "details": string(output)})
			return
		}

		c.JSON(200, gin.H{"msg": "Analysis Completed Successfully"})
	})

	// ── VS Code Extension Workspace Analysis ──────────────────────

	r.POST("/api/analyze-workspace", func(c *gin.Context) {
		var req struct {
			Path string `json:"path"`
		}
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request payload"})
			return
		}

		if req.Path == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "path is required"})
			return
		}

		// Verify target workspace path exists
		if _, err := os.Stat(req.Path); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "workspace path does not exist: " + err.Error()})
			return
		}

		jobID := fmt.Sprintf("job_%d", time.Now().UnixNano())
		job := &Job{
			ID:     jobID,
			Status: "queued",
		}

		jobsMutex.Lock()
		jobs[jobID] = job
		jobsMutex.Unlock()

		// Execute the analysis pipeline in a background goroutine
		go runAnalysisJob(jobID, req.Path)

		c.JSON(http.StatusOK, gin.H{
			"job_id": jobID,
			"msg":    "Preparing project fingerprint...",
		})
	})

	r.GET("/status/:job_id", func(c *gin.Context) {
		jobID := c.Param("job_id")
		jobsMutex.RLock()
		job, exists := jobs[jobID]
		jobsMutex.RUnlock()

		if !exists {
			c.JSON(http.StatusNotFound, gin.H{"error": "job not found"})
			return
		}

		job.Mutex.Lock()
		status := job.Status
		errMsg := job.ErrorMsg
		job.Mutex.Unlock()

		res := gin.H{"status": status}
		if status == "error" {
			res["error"] = errMsg
		}
		c.JSON(http.StatusOK, res)
	})

	r.GET("/progress/:job_id", func(c *gin.Context) {
		jobID := c.Param("job_id")
		jobsMutex.RLock()
		job, exists := jobs[jobID]
		jobsMutex.RUnlock()

		if !exists {
			c.JSON(http.StatusNotFound, gin.H{"error": "job not found"})
			return
		}

		ch := make(chan string, 100)

		job.Mutex.Lock()
		job.Clients = append(job.Clients, ch)
		// Preload existing logs
		existingLogs := make([]string, len(job.Logs))
		copy(existingLogs, job.Logs)
		job.Mutex.Unlock()

		c.Writer.Header().Set("Content-Type", "text/event-stream")
		c.Writer.Header().Set("Cache-Control", "no-cache")
		c.Writer.Header().Set("Connection", "keep-alive")
		c.Writer.Header().Set("Transfer-Encoding", "chunked")

		// Write initial historical logs
		for _, line := range existingLogs {
			fmt.Fprintf(c.Writer, "data: %s\n\n", line)
		}
		c.Writer.Flush()

		c.Stream(func(w io.Writer) bool {
			select {
			case <-c.Request.Context().Done():
				// Client disconnected, unregister channel
				job.Mutex.Lock()
				for i, clientCh := range job.Clients {
					if clientCh == ch {
						job.Clients = append(job.Clients[:i], job.Clients[i+1:]...)
						break
					}
				}
				job.Mutex.Unlock()
				return false
			case line, ok := <-ch:
				if !ok {
					return false
				}
				fmt.Fprintf(w, "data: %s\n\n", line)
				return true
			}
		})
	})

	// ── Reports and Historical Data serving ─────────────────────

	r.GET("/api/history", func(c *gin.Context) {
		patterns := []string{"./ai_report.json", "./json_reports/ai_report_*.json"}
		var files []string
		for _, p := range patterns {
			matches, _ := filepath.Glob(p)
			files = append(files, matches...)
		}

		uniqueReports := make(map[string]HistoryReport)
		for _, f := range files {
			data, err := os.ReadFile(f)
			if err != nil {
				continue
			}
			var report map[string]interface{}
			if err := json.Unmarshal(data, &report); err != nil {
				continue
			}

			reportID, _ := report["report_id"].(string)
			if reportID == "" {
				continue
			}

			projectName, _ := report["project_name"].(string)
			if projectName == "" {
				projectName = "Unnamed Project"
			}

			var score int
			if s, ok := report["overall_score"].(float64); ok {
				score = int(s)
			}

			var issues int
			if iss, ok := report["total_issues"].(float64); ok {
				issues = int(iss)
			}

			timestamp, _ := report["timestamp"].(string)

			uniqueReports[reportID] = HistoryReport{
				ReportID:     reportID,
				ProjectName:  projectName,
				OverallScore: score,
				TotalIssues:  issues,
				Timestamp:    timestamp,
			}
		}

		history := make([]HistoryReport, 0, len(uniqueReports))
		for _, report := range uniqueReports {
			history = append(history, report)
		}

		c.JSON(http.StatusOK, history)
	})

	r.GET("/ai_report", func(c *gin.Context) {
		id := c.Query("id")
		var filePath string
		if id != "" {
			filePath = filepath.Join("./json_reports", fmt.Sprintf("ai_report_%s.json", id))
		} else {
			filePath = "./ai_report.json"
		}

		if _, err := os.Stat(filePath); err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "report not found"})
			return
		}
		c.File(filePath)
	})

	r.GET("/ai_architecture", func(c *gin.Context) {
		id := c.Query("id")
		var filePath string
		if id != "" {
			filePath = filepath.Join("./json_reports", fmt.Sprintf("ai_architecture_%s.json", id))
		} else {
			filePath = "./ai_architecture.json"
		}

		if _, err := os.Stat(filePath); err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "architecture data not found"})
			return
		}
		c.File(filePath)
	})

	r.GET("/dependency_graph", func(c *gin.Context) {
		id := c.Query("id")
		var filePath string
		if id != "" {
			filePath = filepath.Join("./json_reports", fmt.Sprintf("dependency_graph_%s.json", id))
		} else {
			filePath = "./json_reports/dependency_graph.json"
		}

		if _, err := os.Stat(filePath); err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "dependency graph not found"})
			return
		}
		c.File(filePath)
	})

	// Fallback to index.html for frontend HTML5 history mode routing
	r.NoRoute(func(c *gin.Context) {
		c.File("./dist/index.html")
	})

	r.Run(":8081")
}
