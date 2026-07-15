# Threat model

| Asset | Primary risk | Control |
| --- | --- | --- |
| Uploaded files | Code execution | Static inspection only; temporary deletion |
| Scanner endpoints | Abuse and denial of service | Input limits and rate limiting |
| User accounts | Forged login | Server-side Google ID-token verification |
| Scan reports | Privacy leakage | Authenticated history and retention controls |
| Reputation keys | Secret exposure | Environment-only configuration |

This is a defensive scanning tool, not a malware sandbox. Do not send live
malware, confidential documents, or credentials to a deployment you do not own.
