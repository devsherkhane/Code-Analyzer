package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

func RunHistoryTest() {
	patterns := []string{"./json_reports/ai_report.json", "./json_reports/ai_report_*.json"}
	var files []string
	for _, p := range patterns {
		matches, _ := filepath.Glob(p)
		files = append(files, matches...)
	}

	fmt.Printf("Found %d files: %v\n", len(files), files)

	for _, f := range files {
		fmt.Printf("Reading %s...\n", f)
		data, err := os.ReadFile(f)
		if err != nil {
			fmt.Printf("Error reading %s: %v\n", f, err)
			continue
		}
		var report map[string]interface{}
		if err := json.Unmarshal(data, &report); err == nil {
			fmt.Printf("  Success: %v (ID: %v)\n", report["project_name"], report["report_id"])
		} else {
			fmt.Printf("  Error unmarshaling %s: %v\n", f, err)
		}
	}
}
