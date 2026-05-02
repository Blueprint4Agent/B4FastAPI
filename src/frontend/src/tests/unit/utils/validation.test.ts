import { describe, expect, it } from "vitest";

import { isValidEmail, isValidPassword } from "../../../utils/validation";

describe("validation", () => {
    it("accepts a valid email format", () => {
        // Given: email with local/domain sections.
        // When: validation is executed.
        // Then: email is accepted.
        expect(isValidEmail("tester@example.com")).toBe(true);
    });

    it("rejects an invalid email format", () => {
        // Given: malformed email string.
        // When: validation is executed.
        // Then: email is rejected.
        expect(isValidEmail("tester-at-example.com")).toBe(false);
    });

    it("accepts password that satisfies project policy", () => {
        // Given: password with uppercase/number/symbol and valid length.
        // When: validation is executed.
        // Then: password is accepted.
        expect(isValidPassword("ValidPass1!")).toBe(true);
    });

    it("rejects password that does not include uppercase", () => {
        // Given: lowercase-only prefix password.
        // When: validation is executed.
        // Then: password is rejected.
        expect(isValidPassword("invalidpass1!")).toBe(false);
    });
});
