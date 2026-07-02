import { useMemo } from "react";

import { normalizeSystemError } from "../../../api/system/systemError";
import * as systemApi from "../../../api/system/systemApi";

export function useSystemApi() {
    return useMemo(
        () => ({
            ...systemApi,
            normalizeSystemError,
        }),
        [],
    );
}
