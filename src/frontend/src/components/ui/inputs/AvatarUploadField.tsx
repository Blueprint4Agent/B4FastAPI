type AvatarUploadFieldProps = {
    accept?: string;
    busy?: boolean;
    canClear?: boolean;
    helperText?: string;
    onClear: () => void;
    onSelectFile: (file: File | null) => void;
    selectButtonText: string;
    clearButtonText: string;
};

export function AvatarUploadField({
    accept = "image/png,image/jpeg,image/jpg,image/webp,image/gif",
    busy = false,
    canClear = false,
    helperText,
    onClear,
    onSelectFile,
    selectButtonText,
    clearButtonText,
}: AvatarUploadFieldProps) {
    return (
        <div className="avatar-upload-field">
            <div className="avatar-upload-field__actions">
                <label className="avatar-upload-field__button">
                    <span>{selectButtonText}</span>
                    <input
                        type="file"
                        accept={accept}
                        disabled={busy}
                        onChange={(event) => {
                            onSelectFile(event.target.files?.[0] ?? null);
                            event.currentTarget.value = "";
                        }}
                    />
                </label>
                <button
                    type="button"
                    className="avatar-upload-field__button avatar-upload-field__button--ghost"
                    onClick={onClear}
                    disabled={busy || !canClear}
                >
                    {clearButtonText}
                </button>
            </div>
            {helperText ? <p className="avatar-upload-field__helper">{helperText}</p> : null}
        </div>
    );
}
