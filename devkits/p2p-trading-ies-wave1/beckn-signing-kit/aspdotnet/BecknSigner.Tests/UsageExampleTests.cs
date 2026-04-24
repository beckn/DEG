using System.Text;
using BecknSigner;
using Xunit;

namespace BecknSigner.Tests
{
    /// <summary>
    /// These tests demonstrate real-world usage patterns for utility companies.
    /// Each test reads like a recipe: configure, sign, attach to HTTP request.
    /// </summary>
    public class UsageExampleTests
    {
        /// <summary>
        /// The simplest use case: sign a beckn payload and get the Authorization header.
        /// This is the "in goes payload, out comes header" pattern.
        /// </summary>
        [Fact]
        public void Example_SignPayloadForLedgerService()
        {
            // -- Config from your YAML (degledgerrecorder section) --
            var signer = new PayloadSigner(new SignerConfig
            {
                SubscriberId = "p2p-trading-sandbox1.com",
                UniqueKeyId = "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
                SigningPrivateKey = "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=",
            });

            // -- Your beckn payload (confirm, on_confirm, on_status, etc.) --
            string payload = @"{
                ""context"": {
                    ""action"": ""on_confirm"",
                    ""domain"": ""beckn.one:deg:p2p-trading:2.0.0"",
                    ""bap_id"": ""bap.energy-consumer.com""
                },
                ""message"": {
                    ""order"": { ""@type"": ""beckn:Order"", ""beckn:orderStatus"": ""ACTIVE"" }
                }
            }";

            // -- Sign it --
            string authHeader = signer.SignPayload(payload);

            // -- Attach to your HTTP request --
            // using var client = new HttpClient();
            // var request = new HttpRequestMessage(HttpMethod.Post, "https://ledger.example.com/record");
            // request.Content = new StringContent(payload, Encoding.UTF8, "application/json");
            // request.Headers.Add("Authorization", authHeader);
            // var response = await client.SendAsync(request);

            // Verify the header is well-formed
            Assert.StartsWith("Signature keyId=\"p2p-trading-sandbox1.com|76EU8aUq", authHeader);
            Assert.Contains("algorithm=\"ed25519\"", authHeader);
            Assert.Contains("headers=\"(created) (expires) digest\"", authHeader);
        }

        /// <summary>
        /// Verify an incoming signed request from another participant.
        /// </summary>
        [Fact]
        public void Example_VerifyIncomingRequest()
        {
            // Simulate: the sender signs with their private key
            var senderSigner = new PayloadSigner(new SignerConfig
            {
                SubscriberId = "p2p-trading-sandbox3.com",
                UniqueKeyId = "76EU8cNkz3dBEVaR5THuyCciMv9FbA2QqDADHX88WPyYP4v5Cp9ADD",
                SigningPrivateKey = "YW0ObrW6Ca+RLi+rVoxavW6dsC3BuzAx2v9qfutFUcc=",
            });

            string payload = @"{""context"":{""action"":""confirm""},""message"":{}}";
            byte[] body = Encoding.UTF8.GetBytes(payload);
            string authHeader = senderSigner.SignPayload(body);

            // Receiver side: verify using sender's PUBLIC key
            // (In production, you'd look this up from the Beckn DeDi registry)
            string senderPublicKey = "vSAbdarosQEp7CGf18oYIjdG9ewS1gESsmY3TmfzZog=";
            PayloadVerifier.Verify(body, authHeader, senderPublicKey);

            // If we get here, the signature is valid.
            // A tampered payload would throw SignatureVerificationException.
        }
    }
}
