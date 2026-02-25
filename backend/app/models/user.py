from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from app.core.database import Base, get_db

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    auth_record = relationship(
        "AuthRecord", back_populates="user", uselist=False, cascade="all, delete-orphan"
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


class AuthRecord(Base):
    __tablename__ = "auth_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(40), default="email", nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_login_user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user = relationship("User", back_populates="auth_record")


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


class UserDAOError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class UserDAO:
    async def create_signup_user(self, email: str, name: str, password_hash: str) -> UserResponse:
        async with get_db() as db:
            exists_result = await db.execute(select(User.id).where(User.email == email).limit(1))
            if exists_result.first() is not None:
                raise UserDAOError(
                    code="EMAIL_ALREADY_EXISTS",
                    message="User with this email already exists.",
                )

            user = User(email=email, name=name, is_verified=True)
            user.credential = Credential(password_hash=password_hash)
            user.auth_record = AuthRecord(provider="email", identifier=email)
            db.add(user)

            try:
                await db.commit()
                await db.refresh(user)
            except IntegrityError as error:
                await db.rollback()
                raise UserDAOError(
                    code="SIGNUP_FAILED",
                    message="Failed to create the user account.",
                ) from error

            return UserResponse.model_validate(user)

    async def get_auth_user_by_email(self, email: str) -> AuthUserDTO | None:
        async with get_db() as db:
            result = await db.execute(
                select(User)
                .options(selectinload(User.credential), selectinload(User.auth_record))
                .where(User.email == email, User.is_active.is_(True))
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

    async def get_auth_user_by_id(self, user_id: int) -> AuthUserDTO | None:
        async with get_db() as db:
            result = await db.execute(
                select(User)
                .options(selectinload(User.credential))
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

    async def update_login_metadata(
        self,
        user_id: int,
        login_ip: str | None,
        user_agent: str | None,
        login_time: datetime,
    ) -> None:
        async with get_db() as db:
            result = await db.execute(select(AuthRecord).where(AuthRecord.user_id == user_id))
            auth_record = result.scalar_one_or_none()
            if auth_record is None:
                return

            auth_record.last_login_at = login_time
            auth_record.last_login_ip = login_ip
            auth_record.last_login_user_agent = user_agent
            await db.commit()


Users = UserDAO()
