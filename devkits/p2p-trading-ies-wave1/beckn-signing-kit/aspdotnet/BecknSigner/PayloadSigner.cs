using System;
using System.Text;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
using Org.BouncyCastle.Crypto.Digests;

namespace BecknSigner
{
    /// <summary>
    /// Configuration for the Beckn payload signer.
    /// Values come from the simplekeymanager / degledgerrecorder config in your YAML.
    /// </summary>
    public class SignerConfig
    {
        /// <summary>Network participant identifier (e.g. "p2p-trading-sandbox1.com").</summary>
        public string SubscriberId { get; set; }

        /// <summary>Unique key identifier registered with the Beckn registry.</summary>
        public string UniqueKeyId { get; set; }

        /// <summary>Base64-encoded Ed25519 seed (32 bytes).</summary>
        public string SigningPrivateKey { get; set; }

        /// <summary>How long the signature is valid. Defaults to 5 minutes.</summary>
        public TimeSpan ExpiryDuration { get; set; } = TimeSpan.FromMinutes(5);
    }

    /// <summary>
    /// Result of signing a payload.
    /// </summary>
    public class SignedResult
    {
        /// <summary>Full value for the HTTP Authorization header.</summary>
        public string AuthorizationHeader { get; set; }

        /// <summary>Unix timestamp when the signature was created.</summary>
        public long CreatedAt { get; set; }

        /// <summary>Unix timestamp when the signature expires.</summary>
        public long ExpiresAt { get; set; }

        /// <summary>Raw base64-encoded Ed25519 signature.</summary>
        public string Signature { get; set; }
    }

    /// <summary>
    /// Signs Beckn protocol JSON payloads using Ed25519 + BLAKE2-512.
    /// Produces an Authorization header compatible with the Beckn protocol specification.
    /// </summary>
    /// <example>
    /// var signer = new PayloadSigner(new SignerConfig
    /// {
    ///     SubscriberId = "p2p-trading-sandbox1.com",
    ///     UniqueKeyId = "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ",
    ///     SigningPrivateKey = "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw="
    /// });
    ///
    /// string authHeader = signer.SignPayload(payloadBytes);
    /// httpRequest.Headers.Add("Authorization", authHeader);
    /// </example>
    public class PayloadSigner
    {
        private readonly string _subscriberId;
        private readonly string _uniqueKeyId;
        private readonly Ed25519PrivateKeyParameters _privateKey;
        private readonly TimeSpan _expiry;

        public PayloadSigner(SignerConfig config)
        {
            if (config == null)
                throw new ArgumentNullException(nameof(config));
            if (string.IsNullOrEmpty(config.SubscriberId))
                throw new ArgumentException("Value cannot be null or empty.", nameof(config.SubscriberId));
            if (string.IsNullOrEmpty(config.UniqueKeyId))
                throw new ArgumentException("Value cannot be null or empty.", nameof(config.UniqueKeyId));
            if (string.IsNullOrEmpty(config.SigningPrivateKey))
                throw new ArgumentException("Value cannot be null or empty.", nameof(config.SigningPrivateKey));

            var seed = Convert.FromBase64String(config.SigningPrivateKey);
            if (seed.Length != 32)
                throw new ArgumentException($"Private key seed must be 32 bytes, got {seed.Length}");

            _privateKey = new Ed25519PrivateKeyParameters(seed, 0);
            _subscriberId = config.SubscriberId;
            _uniqueKeyId = config.UniqueKeyId;
            _expiry = config.ExpiryDuration;
        }

        /// <summary>
        /// Signs a JSON payload and returns the Authorization header value.
        /// </summary>
        public string SignPayload(byte[] body)
        {
            return SignPayloadDetailed(body).AuthorizationHeader;
        }

        /// <summary>
        /// Signs a JSON payload string and returns the Authorization header value.
        /// </summary>
        public string SignPayload(string body)
        {
            return SignPayload(Encoding.UTF8.GetBytes(body));
        }

        /// <summary>
        /// Signs a JSON payload and returns full signing details.
        /// </summary>
        public SignedResult SignPayloadDetailed(byte[] body)
        {
            return SignPayloadAt(body, DateTimeOffset.UtcNow);
        }

        /// <summary>
        /// Signs at a specific time (useful for deterministic testing).
        /// </summary>
        internal SignedResult SignPayloadAt(byte[] body, DateTimeOffset now)
        {
            long createdAt = now.ToUnixTimeSeconds();
            long expiresAt = now.Add(_expiry).ToUnixTimeSeconds();

            string signingString = BuildSigningString(body, createdAt, expiresAt);
            byte[] signingBytes = Encoding.UTF8.GetBytes(signingString);

            // Ed25519 sign
            var edSigner = new Ed25519Signer();
            edSigner.Init(true, _privateKey);
            edSigner.BlockUpdate(signingBytes, 0, signingBytes.Length);
            byte[] signatureBytes = edSigner.GenerateSignature();

            string signature = Convert.ToBase64String(signatureBytes);

            string header = $"Signature keyId=\"{_subscriberId}|{_uniqueKeyId}|ed25519\"," +
                            $"algorithm=\"ed25519\"," +
                            $"created=\"{createdAt}\"," +
                            $"expires=\"{expiresAt}\"," +
                            $"headers=\"(created) (expires) digest\"," +
                            $"signature=\"{signature}\"";

            return new SignedResult
            {
                AuthorizationHeader = header,
                CreatedAt = createdAt,
                ExpiresAt = expiresAt,
                Signature = signature,
            };
        }

        internal static string BuildSigningString(byte[] body, long createdAt, long expiresAt)
        {
            byte[] hash = Blake2bHash(body);
            string digestB64 = Convert.ToBase64String(hash);
            return $"(created): {createdAt}\n(expires): {expiresAt}\ndigest: BLAKE-512={digestB64}";
        }

        private static byte[] Blake2bHash(byte[] data)
        {
            var digest = new Blake2bDigest(512);
            digest.BlockUpdate(data, 0, data.Length);
            byte[] hash = new byte[64]; // 512 bits = 64 bytes
            digest.DoFinal(hash, 0);
            return hash;
        }
    }
}
