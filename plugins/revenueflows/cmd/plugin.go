// Package main provides the plugin entry point for the RevenueFlows plugin.
// Compiled as a Go plugin (.so) and loaded by beckn-onix at runtime.
package main

import (
	"context"

	"github.com/beckn-one/beckn-onix/pkg/plugin/definition"
	revenueflows "github.com/beckn-one/deg/plugins/revenueflows"
)

type provider struct{}

func (p provider) New(ctx context.Context, cfg map[string]string) (definition.Step, func(), error) {
	rf, err := revenueflows.New(cfg)
	if err != nil {
		return nil, nil, err
	}
	return rf, rf.Close, nil
}

// Provider is the exported symbol that beckn-onix plugin manager looks up.
var Provider = provider{}
