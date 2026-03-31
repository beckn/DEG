// Package main provides the plugin entry point for the RevenueFlows middleware.
// Compiled as a Go plugin (.so) and loaded by beckn-onix at runtime.
package main

import (
	"context"
	"net/http"

	revenueflows "github.com/beckn-one/deg/plugins/revenueflows"
)

type provider struct{}

func (p provider) New(ctx context.Context, cfg map[string]string) (func(http.Handler) http.Handler, error) {
	return revenueflows.NewMiddleware(cfg)
}

// Provider is the exported symbol that beckn-onix plugin manager looks up.
var Provider = provider{}
