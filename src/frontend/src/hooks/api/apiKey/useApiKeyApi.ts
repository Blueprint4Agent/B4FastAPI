import { useMemo } from "react";

import * as apiKeyApi from "../../../api/apiKey/apiKeyApi";
import {
    extractAPIKeyErrorDetail,
    resolveAPIKeyErrorMessage,
} from "../../../api/apiKey/apiKeyError";

export type { APIKeyRecord } from "../../../api/apiKey/apiKeyApi";

export function useApiKeyApi() {
    return useMemo(
        () => ({
            ...apiKeyApi,
            extractAPIKeyErrorDetail,
            resolveAPIKeyErrorMessage,
        }),
        [],
    );
}
