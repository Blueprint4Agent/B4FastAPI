import { getCurrentWindow } from "@tauri-apps/api/window";
import type { MouseEvent as ReactMouseEvent } from "react";

import { isTauriRuntime } from "./desktopRuntime";

const INTERACTIVE_SELECTOR = "a, button, input, select, textarea, [role='button'], [role='menu']";

export function startDesktopWindowDrag(event: ReactMouseEvent<HTMLElement>) {
    if (event.button !== 0 || !isTauriRuntime(window)) return;

    const target = event.target;
    if (target instanceof Element && target.closest(INTERACTIVE_SELECTOR)) return;

    event.preventDefault();
    void getCurrentWindow()
        .startDragging()
        .catch((error: unknown) => console.error("Desktop window drag failed.", error));
}
