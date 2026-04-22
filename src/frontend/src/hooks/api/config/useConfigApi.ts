import { useMemo } from "react";

import { getConfig } from "../../../api/config/configApi";
import {
    extractConfigErrorMessage,
    resolveConfigErrorMessage,
} from "../../../api/config/configError";

export function useConfigApi() {
    return useMemo(
        () => ({
            getConfig,
            extractConfigErrorMessage,
            resolveConfigErrorMessage,
        }),
        [],
    );
}
