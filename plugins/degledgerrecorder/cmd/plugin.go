// Package main provides the plugin entry point for the DEG Ledger Recorder plugin.
// This file is compiled as a Go plugin (.so) and loaded by beckn-onix at runtime.
package main

import (
	"context"

	"github.com/beckn-one/beckn-onix/pkg/plugin/definition"
	degledgerrecorder "github.com/beckn-one/deg/plugins/degledgerrecorder"
)

// provider implements the StepProvider interface for plugin loading.
type provider struct{}

// New creates a new DEGLedgerRecorder step instance.
// It returns the step, a cleanup function, and any error.
func (p provider) New(ctx context.Context, cfg map[string]string) (definition.Step, func(), error) {
	recorder, err := degledgerrecorder.New(cfg)
	if err != nil {
		return nil, nil, err
	}

	// Return the recorder, its Close method as cleanup, and no error
	return recorder, recorder.Close, nil
}

// Provider is the exported symbol that beckn-onix plugin manager looks up.
// It must be a package-level variable named "Provider".
var Provider = provider{}
