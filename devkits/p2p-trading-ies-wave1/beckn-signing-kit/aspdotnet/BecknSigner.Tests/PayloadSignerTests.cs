using System;
using System.Text;
using BecknSigner;
using Xunit;

namespace BecknSigner.Tests
{
    /// <summary>
    /// Tests using the same keys as local-p2p-bap.yaml (sandbox1).
    /// </summary>
    public class PayloadSignerTests
    {
        private const string TestSubscriberId = "p2p-trading-sandbox1.com";
        private const string TestKeyId = "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ";
        private const string TestPrivateKey = "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=";
        private const string TestPublicKey = "KVYEWkQB2WwnttVMWfy7KrnqiD51ZDvi8vfCac2IwRE=";

        private static readonly string SamplePayload = @"{
  ""context"": {
    ""version"": ""2.0.0"",
    ""action"": ""confirm"",
    ""timestamp"": ""2024-10-04T10:25:00Z"",
    ""message_id"": ""msg-confirm-001"",
    ""transaction_id"": ""txn-energy-001"",
    ""bap_id"": ""bap.energy-consumer.com"",
    ""bap_uri"": ""https://bap.energy-consumer.com"",
    ""bpp_id"": ""bpp.energy-provider.com"",
    ""bpp_uri"": ""https://bpp.energy-provider.com"",
    ""domain"": ""beckn.one:deg:p2p-trading:2.0.0""
  },
  ""message"": {
    ""order"": {
      ""@type"": ""beckn:Order"",
      ""beckn:orderStatus"": ""CREATED"",
      ""beckn:seller"": ""provider-solar-farm-001""
    }
  }
}";

        private PayloadSigner CreateSigner()
        {
            return new PayloadSigner(new SignerConfig
            {
                SubscriberId = TestSubscriberId,
                UniqueKeyId = TestKeyId,
                SigningPrivateKey = TestPrivateKey,
            });
        }

        [Fact]
        public void SignAndVerify_RoundTrip_Succeeds()
        {
            var signer = CreateSigner();
            var body = Encoding.UTF8.GetBytes(SamplePayload);

            string authHeader = signer.SignPayload(body);

            // Structure checks
            Assert.StartsWith("Signature ", authHeader);
            Assert.Contains(TestSubscriberId + "|" + TestKeyId + "|ed25519", authHeader);
            Assert.Contains("algorithm=\"ed25519\"", authHeader);

            // Verify succeeds
            PayloadVerifier.Verify(body, authHeader, TestPublicKey);
        }

        [Fact]
        public void SignPayload_StringOverload_ProducesSameResult()
        {
            var signer = CreateSigner();

            // String and byte[] should produce valid signatures
            string authFromString = signer.SignPayload(SamplePayload);
            Assert.StartsWith("Signature ", authFromString);

            var body = Encoding.UTF8.GetBytes(SamplePayload);
            PayloadVerifier.Verify(body, authFromString, TestPublicKey);
        }

        [Fact]
        public void SignPayloadDetailed_Returns300SecondWindow()
        {
            var signer = CreateSigner();
            var body = Encoding.UTF8.GetBytes(SamplePayload);

            var result = signer.SignPayloadDetailed(body);

            Assert.Equal(300, result.ExpiresAt - result.CreatedAt);
            Assert.NotEmpty(result.Signature);
            Assert.NotEmpty(result.AuthorizationHeader);
        }

        [Fact]
        public void Verify_RejectsTamperedPayload()
        {
            var signer = CreateSigner();
            var body = Encoding.UTF8.GetBytes(SamplePayload);

            string authHeader = signer.SignPayload(body);

            // Tamper
            var tampered = Encoding.UTF8.GetBytes(SamplePayload.Replace("confirm", "cancel"));

            Assert.Throws<SignatureVerificationException>(
                () => PayloadVerifier.Verify(tampered, authHeader, TestPublicKey));
        }

        [Fact]
        public void Verify_RejectsExpiredSignature()
        {
            var signer = new PayloadSigner(new SignerConfig
            {
                SubscriberId = TestSubscriberId,
                UniqueKeyId = TestKeyId,
                SigningPrivateKey = TestPrivateKey,
                ExpiryDuration = TimeSpan.FromSeconds(1),
            });
            var body = Encoding.UTF8.GetBytes(SamplePayload);

            // Sign in the past
            var past = DateTimeOffset.UtcNow.AddMinutes(-10);
            var result = signer.SignPayloadAt(body, past);

            var ex = Assert.Throws<SignatureVerificationException>(
                () => PayloadVerifier.Verify(body, result.AuthorizationHeader, TestPublicKey));
            Assert.Contains("expired", ex.Message, StringComparison.OrdinalIgnoreCase);
        }

        [Fact]
        public void Verify_RejectsWrongPublicKey()
        {
            var signer = CreateSigner();
            var body = Encoding.UTF8.GetBytes(SamplePayload);

            string authHeader = signer.SignPayload(body);

            // Use sandbox3 public key instead of sandbox1
            string wrongPublicKey = "vSAbdarosQEp7CGf18oYIjdG9ewS1gESsmY3TmfzZog=";

            Assert.Throws<SignatureVerificationException>(
                () => PayloadVerifier.Verify(body, authHeader, wrongPublicKey));
        }

        [Fact]
        public void Constructor_ValidatesConfig()
        {
            Assert.Throws<ArgumentException>(() => new PayloadSigner(new SignerConfig
            {
                SubscriberId = "",
                UniqueKeyId = TestKeyId,
                SigningPrivateKey = TestPrivateKey,
            }));

            Assert.Throws<ArgumentException>(() => new PayloadSigner(new SignerConfig
            {
                SubscriberId = TestSubscriberId,
                UniqueKeyId = TestKeyId,
                SigningPrivateKey = Convert.ToBase64String(new byte[] { 1, 2, 3 }), // wrong size
            }));
        }

        [Fact]
        public void ParseKeyId_WorksCorrectly()
        {
            var parsed = PayloadVerifier.ParseKeyId("p2p-trading-sandbox1.com|76EU8aUq|ed25519");
            Assert.Equal("p2p-trading-sandbox1.com", parsed.SubscriberId);
            Assert.Equal("76EU8aUq", parsed.UniqueKeyId);
            Assert.Equal("ed25519", parsed.Algorithm);

            Assert.Throws<ArgumentException>(() => PayloadVerifier.ParseKeyId("bad-format"));
        }
    }
}
