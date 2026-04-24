using System;
using System.Collections.Generic;
using System.Text;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;

namespace BecknSigner
{
    /// <summary>
    /// Verifies Beckn protocol Authorization header signatures.
    /// </summary>
    public static class PayloadVerifier
    {
        /// <summary>
        /// Verifies that the Authorization header is a valid signature for the given body.
        /// </summary>
        /// <param name="body">The raw JSON payload bytes.</param>
        /// <param name="authHeader">The full Authorization header value.</param>
        /// <param name="publicKeyBase64">The sender's base64-encoded Ed25519 public key.</param>
        /// <exception cref="SignatureVerificationException">If verification fails.</exception>
        public static void Verify(byte[] body, string authHeader, string publicKeyBase64)
        {
            VerifyAt(body, authHeader, publicKeyBase64, DateTimeOffset.UtcNow);
        }

        /// <summary>
        /// Verifies at a specific time (useful for testing).
        /// </summary>
        public static void VerifyAt(byte[] body, string authHeader, string publicKeyBase64, DateTimeOffset now)
        {
            long created, expires;
            string signature;
            ParseAuthHeader(authHeader, out created, out expires, out signature);

            long currentTime = now.ToUnixTimeSeconds();
            if (created > currentTime)
                throw new SignatureVerificationException($"Signature not yet valid (created {created} > now {currentTime})");
            if (currentTime > expires)
                throw new SignatureVerificationException($"Signature expired (expires {expires} < now {currentTime})");

            byte[] signatureBytes = Convert.FromBase64String(signature);
            string signingString = PayloadSigner.BuildSigningString(body, created, expires);
            byte[] signingBytes = Encoding.UTF8.GetBytes(signingString);

            byte[] publicKeyBytes = Convert.FromBase64String(publicKeyBase64);
            var publicKey = new Ed25519PublicKeyParameters(publicKeyBytes, 0);

            var verifier = new Ed25519Signer();
            verifier.Init(false, publicKey);
            verifier.BlockUpdate(signingBytes, 0, signingBytes.Length);

            if (!verifier.VerifySignature(signatureBytes))
                throw new SignatureVerificationException("Signature verification failed");
        }

        /// <summary>
        /// Parses the keyId field from an Authorization header.
        /// Format: "subscriber_id|unique_key_id|algorithm"
        /// </summary>
        public static ParsedKeyId ParseKeyId(string keyId)
        {
            var parts = keyId.Split('|');
            if (parts.Length != 3)
                throw new ArgumentException($"Invalid keyId format, expected 'subscriber|keyId|algorithm', got '{keyId}'");
            return new ParsedKeyId(parts[0], parts[1], parts[2]);
        }

        private static void ParseAuthHeader(string header, out long created, out long expires, out string signature)
        {
            if (header.StartsWith("Signature ", StringComparison.OrdinalIgnoreCase))
                header = header.Substring("Signature ".Length);

            var parameters = new Dictionary<string, string>();
            foreach (var part in header.Split(','))
            {
                var eqIndex = part.IndexOf('=');
                if (eqIndex > 0)
                {
                    string key = part.Substring(0, eqIndex).Trim();
                    string value = part.Substring(eqIndex + 1).Trim().Trim('"');
                    parameters[key] = value;
                }
            }

            string createdStr;
            if (!parameters.TryGetValue("created", out createdStr) || !long.TryParse(createdStr, out created))
                throw new SignatureVerificationException("Missing or invalid 'created' in auth header");

            string expiresStr;
            if (!parameters.TryGetValue("expires", out expiresStr) || !long.TryParse(expiresStr, out expires))
                throw new SignatureVerificationException("Missing or invalid 'expires' in auth header");

            if (!parameters.TryGetValue("signature", out signature))
                throw new SignatureVerificationException("Missing 'signature' in auth header");
        }
    }

    /// <summary>
    /// Result of parsing a keyId string from an Authorization header.
    /// </summary>
    public class ParsedKeyId
    {
        public string SubscriberId { get; }
        public string UniqueKeyId { get; }
        public string Algorithm { get; }

        public ParsedKeyId(string subscriberId, string uniqueKeyId, string algorithm)
        {
            SubscriberId = subscriberId;
            UniqueKeyId = uniqueKeyId;
            Algorithm = algorithm;
        }
    }

    public class SignatureVerificationException : Exception
    {
        public SignatureVerificationException(string message) : base(message) { }
    }
}
