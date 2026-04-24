package signer_test

import (
	"fmt"
	"log"
	"net/http"
	"strings"

	signer "github.com/beckn/deg-discom-signing-kit"
)

func Example_signAndSend() {
	// 1. Configure the signer with your keys from the YAML config.
	//    These come from the simplekeymanager / degledgerrecorder config.
	s, err := signer.New(signer.Config{
		SubscriberID:     "p2p-trading-sandbox1.com",
		UniqueKeyID:      "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
		SigningPrivateKey: "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=",
	})
	if err != nil {
		log.Fatal(err)
	}

	// 2. Your beckn JSON payload (confirm, on_confirm, on_status, etc.)
	payload := []byte(`{
		"context": {
			"action": "confirm",
			"domain": "beckn.one:deg:p2p-trading:2.0.0",
			"bap_id": "bap.energy-consumer.com"
		},
		"message": {
			"order": { "@type": "beckn:Order", "beckn:orderStatus": "CREATED" }
		}
	}`)

	// 3. Sign it — this is the entire SDK surface.
	authHeader, err := s.SignPayload(payload)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Authorization header generated:")
	fmt.Println(authHeader[:50] + "...")

	// 4. Attach to HTTP request (e.g., posting to ledger service).
	req, _ := http.NewRequest("POST", "https://ledger.example.com/record", strings.NewReader(string(payload)))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", authHeader)

	// req is now ready to send.
	_ = req

	// Output:
	// Authorization header generated:
	// Signature keyId="p2p-trading-sandbox1.com|76EU8aUq...
}

func Example_verify() {
	// Verifier side: validate an incoming signed request.
	payload := []byte(`{"context":{"action":"confirm"}}`)

	// First sign (simulating sender)
	s, _ := signer.New(signer.Config{
		SubscriberID:     "p2p-trading-sandbox1.com",
		UniqueKeyID:      "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
		SigningPrivateKey: "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=",
	})
	authHeader, _ := s.SignPayload(payload)

	// Verify (receiver side — you'd look up the public key from registry)
	senderPublicKey := "KVYEWkQB2WwnttVMWfy7KrnqiD51ZDvi8vfCac2IwRE="
	err := signer.Verify(payload, authHeader, senderPublicKey)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Signature valid!")

	// Output:
	// Signature valid!
}
