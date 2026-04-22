import { useMemo } from "react";

import * as authApi from "../../../api/auth/authApi";
import { extractApiDetail, resolveAuthErrorMessage } from "../../../api/auth/authError";

export type { OAuthProvider } from "../../../api/auth/authApi";

export function useAuthApi() {
    return useMemo(
        () => ({
            ...authApi,
            extractApiDetail,
            resolveAuthErrorMessage,
        }),
        [],
    );
}
