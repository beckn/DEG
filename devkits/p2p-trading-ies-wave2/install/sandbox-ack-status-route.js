const fs = require("fs");

const webhookControllerPath =
  process.env.SANDBOX_WEBHOOK_CONTROLLER_PATH || "/app/dist/webhook/controller.js";
let webhookController = fs.readFileSync(webhookControllerPath, "utf8");

// The stock sandbox /api/webhook/status handler emits an on_status callback.
// In Wave 2, degledgerrecorder owns that DISCOM cascade, so the sandbox should
// only log and ACK status while keeping normal webhook routing visible.
const ackOnlyStatusHandler = `const onStatus = (req, res) => {
    const { context, message } = req.body;
    console.log(JSON.stringify({ message, context }, null, 2));
    return res.status(200).json(buildAck(context));
};
exports.onStatus = onStatus;`;

if (!webhookController.includes("sandbox ACK-only status customization")) {
  webhookController = webhookController.replace(
    /const onStatus = \(req, res\) => \{[\s\S]*?\};\nexports\.onStatus = onStatus;/,
    `// sandbox ACK-only status customization\n${ackOnlyStatusHandler}`
  );
  fs.writeFileSync(webhookControllerPath, webhookController);
  console.log("sandbox startup: made /api/webhook/status ACK-only");
} else {
  console.log("sandbox startup: /api/webhook/status is already ACK-only");
}

// Static seller fixtures contain example platform identities. For init and
// confirm, inherit the roles and participants from the incoming request so the
// generated on_* response remains consistent with context.bapId/context.bppId.
const contractPartyMarker = "sandbox init/confirm contract party inheritance";
const contractPartyHelper = `// ${contractPartyMarker}
const cloneContractParties = (value) => JSON.parse(JSON.stringify(value));
const inheritContractParties = (responsePayload, requestMessage) => {
    const requestContract = requestMessage?.contract;
    const responseContract = responsePayload?.message?.contract;
    const roles = requestContract?.contractAttributes?.roles;
    const participants = requestContract?.participants;

    if (!responseContract || !Array.isArray(roles) || !Array.isArray(participants)) {
        console.warn("sandbox response: request is missing contract roles or participants; using fixture values");
        return responsePayload;
    }

    responseContract.contractAttributes = {
        ...(responseContract.contractAttributes || {}),
        roles: cloneContractParties(roles),
    };
    responseContract.participants = cloneContractParties(participants);
    console.log("sandbox response: inherited contract roles and participants from request");
    return responsePayload;
};
`;

const wrapResponsePayload = (source, action) => {
  const responsePayloadPattern = new RegExp(
    `const responsePayload = \\{\\s*\\.\\.\\.template,\\s*context: buildResponseContext\\(context, "${action}"\\),?\\s*\\};`
  );

  if (!responsePayloadPattern.test(source)) {
    throw new Error(`sandbox startup: could not find ${action} response payload builder`);
  }

  return source.replace(
    responsePayloadPattern,
    `const responsePayload = inheritContractParties({
                ...template,
                context: buildResponseContext(context, "${action}"),
            }, message);`
  );
};

if (!webhookController.includes(contractPartyMarker)) {
  const onInitDeclaration = "const onInit = (req, res) => {";
  if (!webhookController.includes(onInitDeclaration)) {
    throw new Error("sandbox startup: could not find init handler");
  }

  webhookController = webhookController.replace(
    onInitDeclaration,
    `${contractPartyHelper}\n${onInitDeclaration}`
  );
  webhookController = wrapResponsePayload(webhookController, "init");
  webhookController = wrapResponsePayload(webhookController, "confirm");
  fs.writeFileSync(webhookControllerPath, webhookController);
  console.log("sandbox startup: init/confirm responses now inherit request contract parties");
} else {
  console.log("sandbox startup: init/confirm contract parties already inherit from requests");
}
