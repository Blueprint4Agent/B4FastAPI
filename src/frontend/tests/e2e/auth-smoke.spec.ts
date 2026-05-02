import { expect, test } from "@playwright/test";

test("login page route renders", async ({ page }) => {
    // Given: frontend dev server is running.
    // When: login route is opened.
    await page.goto("/login");

    // Then: login title and submit button are visible.
    await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});
