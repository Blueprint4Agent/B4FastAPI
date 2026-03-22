from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from app.core.database import Base, get_db
from app.core.error import AuthErrorCode, AuthException

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    credential = relationship(
        "Credential", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    auth_identities = relationship(
        "AuthIdentity", back_populates="user", cascade="all, delete-orphan"
    )


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User", back_populates="credential")


class AuthIdentity(Base):
    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "identifier", name="uq_auth_identities_provider_identifier"),
        UniqueConstraint("user_id", "provider", name="uq_auth_identities_user_provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="email", nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_login_user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user = relationship("User", back_populates="auth_identities")


class SignupForm(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    name: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=24)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one number.")
        if not any(not char.isalnum() for char in value):
            raise ValueError("Password must include at least one symbol.")
        if any(char.isspace() for char in value):
            raise ValueError("Password cannot contain spaces.")
        return value


class LoginForm(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    password: str = Field(min_length=8, max_length=24)
    remember_me: bool = False


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerifyEmailForm(BaseModel):
    token: str = Field(min_length=16, max_length=512)


class VerifyEmailResponse(BaseModel):
    message: str
    user: UserResponse


class ResendVerificationForm(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)


class ResendVerificationResponse(BaseModel):
    message: str


class ForgotPasswordForm(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordForm(BaseModel):
    token: str = Field(min_length=16, max_length=512)
    password: str = Field(min_length=8, max_length=24)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one number.")
        if not any(not char.isalnum() for char in value):
            raise ValueError("Password must include at least one symbol.")
        if any(char.isspace() for char in value):
            raise ValueError("Password cannot contain spaces.")
        return value


class ResetPasswordResponse(BaseModel):
    message: str


class APIError(BaseModel):
    error: str
    message: str
    details: dict | None = None


class AuthUserDTO(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    password_hash: str | None = None

    def as_user_response(self) -> UserResponse:
        return UserResponse(
            id=self.id,
            email=self.email,
            name=self.name,
            is_verified=self.is_verified,
            created_at=self.created_at,
        )


class UserRepository:
    async def create_signup_user(
        self,
        email: str,
        name: str,
        password_hash: str,
        is_verified: bool = False,
    ) -> UserResponse:
        async with get_db() as db:
            existing = await db.execute(select(User.id).where(User.email == email).limit(1))
            if existing.first() is not None:
                raise AuthException(code=AuthErrorCode.EMAIL_ALREADY_EXISTS)

            user = User(email=email, name=name, is_verified=is_verified)
            user.credential = Credential(password_hash=password_hash)
            user.auth_identities = [AuthIdentity(provider="email", identifier=email)]
            db.add(user)

            try:
                await db.commit()
                await db.refresh(user)
            except IntegrityError:
                await db.rollback()
                raise

            return UserResponse.model_validate(user)

    async def create_oauth_user(
        self,
        email: str,
        name: str,
        provider: str,
        identifier: str,
        is_verified: bool = True,
    ) -> UserResponse:
        async with get_db() as db:
            existing = await db.execute(select(User.id).where(User.email == email).limit(1))
            if existing.first() is not None:
                raise AuthException(code=AuthErrorCode.EMAIL_ALREADY_EXISTS)

            user = User(email=email, name=name, is_verified=is_verified)
            user.auth_identities = [AuthIdentity(provider=provider, identifier=identifier)]
            db.add(user)

            try:
                await db.commit()
                await db.refresh(user)
            except IntegrityError:
                await db.rollback()
                raise

            return UserResponse.model_validate(user)

    async def get_auth_user_by_identity(self, provider: str, identifier: str) -> AuthUserDTO | None:
        async with get_db() as db:
            result = await db.execute(
                select(User)
                .join(AuthIdentity, AuthIdentity.user_id == User.id)
                .options(selectinload(User.credential), selectinload(User.auth_identities))
                .where(
                    AuthIdentity.provider == provider,
                    AuthIdentity.identifier == identifier,
                    User.is_active.is_(True),
                )
            )
            user = result.scalar_one_or_none()

        if user is None:
            return None

        return AuthUserDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            password_hash=user.credential.password_hash if user.credential else None,
        )

    async def get_auth_user_by_email(self, email: str) -> AuthUserDTO | None:
        return await self.get_auth_user_by_identity(provider="email", identifier=email)

    async def get_user_response_by_email(self, email: str) -> UserResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(User).where(User.email == email, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None
            return UserResponse.model_validate(user)

    async def get_auth_user_by_id(self, user_id: int) -> AuthUserDTO | None:
        async with get_db() as db:
            result = await db.execute(
                select(User)
                .options(selectinload(User.credential), selectinload(User.auth_identities))
                .where(User.id == user_id, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()

        if user is None:
            return None

        return AuthUserDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            password_hash=user.credential.password_hash if user.credential else None,
        )

    async def get_user_response_by_id(self, user_id: int) -> UserResponse | None:
        auth_user = await self.get_auth_user_by_id(user_id)
        if auth_user is None:
            return None
        return auth_user.as_user_response()

    async def link_auth_identity(self, user_id: int, provider: str, identifier: str) -> bool:
        async with get_db() as db:
            auth_identity = AuthIdentity(
                user_id=user_id,
                provider=provider,
                identifier=identifier,
            )
            db.add(auth_identity)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                return False
        return True

    async def update_login_metadata(
        self,
        user_id: int,
        provider: str,
        identifier: str,
        login_ip: str | None,
        user_agent: str | None,
        login_time: datetime,
    ) -> None:
        async with get_db() as db:
            result = await db.execute(
                select(AuthIdentity).where(
                    AuthIdentity.user_id == user_id,
                    AuthIdentity.provider == provider,
                    AuthIdentity.identifier == identifier,
                )
            )
            auth_identity = result.scalar_one_or_none()
            if auth_identity is None:
                return

            auth_identity.last_login_at = login_time
            auth_identity.last_login_ip = login_ip
            auth_identity.last_login_user_agent = user_agent
            await db.commit()

    async def mark_email_verified(self, user_id: int) -> UserResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(User).where(User.id == user_id, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None

            user.is_verified = True
            await db.commit()
            await db.refresh(user)
            return UserResponse.model_validate(user)

    async def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        async with get_db() as db:
            result = await db.execute(
                select(Credential)
                .join(User, User.id == Credential.user_id)
                .where(User.id == user_id, User.is_active.is_(True))
            )
            credential = result.scalar_one_or_none()
            if credential is None:
                return False

            credential.password_hash = password_hash
            credential.updated_at = datetime.now(UTC)
            await db.commit()
            return True


Users = UserRepository()
