const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_PATTERN = /^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9])\S{8,24}$/;

export function isValidEmail(value: string): boolean {
    return EMAIL_PATTERN.test(value.trim());
}

export function isValidPassword(value: string): boolean {
    return PASSWORD_PATTERN.test(value);
}
