import { useTranslation } from "react-i18next";
import { useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import { ErrorCard, InfoCard, WarningCard } from "../components/StatusCard";
import { useTheme } from "../hooks/useTheme";
import {
  BrandMark,
  Button,
  DropdownMenu,
  FormCheckbox,
  InputField,
  KeyValueCard,
  OAuthOptionsCard,
  OAuthProviderButton,
  PanelCard,
  Spinner,
  ThemeToggleButton,
  ValidationCard
} from "../components/ui";
import { useAuthContext } from "../hooks/useAuth";

function ShowcaseItem({
  component,
  children,
  className
}: {
  component: string;
  children: ReactNode;
  className?: string;
}) {
  const nextClassName = className ? `showcase-item ${className}` : "showcase-item";
  return (
    <div className={nextClassName} data-component={component}>
      <p className="showcase-item__name">{component}</p>
      <div className="showcase-item__preview">{children}</div>
    </div>
  );
}

export function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuthContext();
  const navigate = useNavigate();
  const { themeMode, setThemeMode } = useTheme();
  const [sampleInput, setSampleInput] = useState("");
  const [sampleChecked, setSampleChecked] = useState(true);

  return (
    <section className="dashboard-catalog">
      <header className="dashboard-catalog__header">
        <h1>{t("dashboard.title")}</h1>
        <p>{t("dashboard.subtitle")}</p>
      </header>

      <section className="dashboard-catalog__group">
        <h2>Buttons & Components</h2>
        <div className="dashboard-catalog__components">
          <div className="dashboard-catalog__section-card">
            <h3>Brand & Theme</h3>
            <div className="dashboard-catalog__row">
              <ShowcaseItem component="BrandMark">
                <BrandMark />
              </ShowcaseItem>
              <ShowcaseItem component="ThemeToggleButton">
                <ThemeToggleButton themeMode={themeMode} onChangeTheme={setThemeMode} />
              </ShowcaseItem>
            </div>
          </div>

          <div className="dashboard-catalog__section-card">
            <h3>Buttons</h3>
            <div className="dashboard-catalog__row">
              <ShowcaseItem component="Button">
                <Button>Primary button</Button>
              </ShowcaseItem>
              <ShowcaseItem component="Button (loading)">
                <Button loading>Loading button</Button>
              </ShowcaseItem>
              <ShowcaseItem component="Button (disabled)">
                <Button disabled>Disabled button</Button>
              </ShowcaseItem>
              <ShowcaseItem component="OAuthProviderButton (google/github)">
                <div className="dashboard-catalog__oauth-row">
                  <OAuthProviderButton
                    provider="google"
                    label="Continue with Google"
                    startPath="/show-case"
                  />
                  <OAuthProviderButton
                    provider="github"
                    label="Continue with GitHub"
                    startPath="/show-case"
                  />
                </div>
              </ShowcaseItem>
            </div>
          </div>

          <div className="dashboard-catalog__section-card">
            <h3>Dropdown</h3>
            <div className="dashboard-catalog__row">
              <ShowcaseItem component="DropdownMenu">
                <DropdownMenu
                  triggerLabel="Open menu"
                  label="Demo dropdown"
                  items={[
                    { id: "item-1", label: "Item 1" },
                    { id: "item-2", label: "Item 2" },
                    { id: "item-3", label: "Item 3" }
                  ]}
                />
              </ShowcaseItem>
            </div>
          </div>

          <div className="dashboard-catalog__section-card">
            <h3>Inputs</h3>
            <div className="dashboard-catalog__stack">
              <ShowcaseItem component="InputField">
                <InputField
                  label="Sample input"
                  value={sampleInput}
                  onValueChange={setSampleInput}
                  placeholder="Type something..."
                />
              </ShowcaseItem>
              <ShowcaseItem component="FormCheckbox">
                <FormCheckbox
                  checked={sampleChecked}
                  onCheckedChange={setSampleChecked}
                  label="Sample checkbox"
                />
              </ShowcaseItem>
            </div>
          </div>

          <div className="dashboard-catalog__section-card">
            <h3>Spinners</h3>
            <div className="dashboard-catalog__row">
              <ShowcaseItem component="Spinner (sm)">
                <Spinner size="sm" label="Small spinner" />
              </ShowcaseItem>
              <ShowcaseItem component="Spinner (md)">
                <Spinner size="md" label="Medium spinner" />
              </ShowcaseItem>
              <ShowcaseItem component="Spinner (lg)">
                <Spinner size="lg" label="Large spinner" />
              </ShowcaseItem>
            </div>
          </div>

          <div className="dashboard-catalog__section-card">
            <h3>Pages</h3>
            <div className="dashboard-catalog__row">
              <ShowcaseItem component="LoadingPage">
                <Button type="button" onClick={() => navigate("/show-case/loading")}>
                  Open loading page
                </Button>
              </ShowcaseItem>
              <ShowcaseItem component="ShowCaseNotFoundPage">
                <Button type="button" onClick={() => navigate("/show-case/404")}>
                  Open 404 page
                </Button>
              </ShowcaseItem>
            </div>
          </div>
        </div>
      </section>

      <section className="dashboard-catalog__group">
        <h2>Cards</h2>
        <div className="dashboard-catalog__cards">
          <ShowcaseItem component="PanelCard" className="dashboard-catalog__panel-demo">
            <PanelCard
              title="Panel Card"
              subtitle="Generic container card used across auth screens."
            >
              <p className="muted">Reusable top-level card sample.</p>
            </PanelCard>
          </ShowcaseItem>
          <ShowcaseItem component="KeyValueCard">
            <dl className="meta">
              <KeyValueCard label={t("dashboard.labels.userId")} value={user?.id ?? "-"} />
              <KeyValueCard label={t("dashboard.labels.name")} value={user?.name ?? "-"} />
              <KeyValueCard label={t("dashboard.labels.email")} value={user?.email ?? "-"} />
            </dl>
          </ShowcaseItem>
          <ShowcaseItem component="InfoCard">
            <InfoCard title="Info" message="Information status card example." />
          </ShowcaseItem>
          <ShowcaseItem component="WarningCard">
            <WarningCard title="Warning" message="Warning status card example." />
          </ShowcaseItem>
          <ShowcaseItem component="ErrorCard">
            <ErrorCard title="Error" message="Error status card example." />
          </ShowcaseItem>
          <ShowcaseItem component="ValidationCard">
            <ValidationCard
              title="Validation sample"
              rules={[
                { isValid: true, label: "Contains uppercase" },
                { isValid: true, label: "Contains number" },
                { isValid: false, label: "Contains special character" }
              ]}
            />
          </ShowcaseItem>
          <ShowcaseItem component="OAuthOptionsCard">
            <OAuthOptionsCard title="Option Card">
              <div className="dashboard-catalog__stack">
                <Button type="button">Option item 1</Button>
                <Button type="button">Option item 2</Button>
              </div>
            </OAuthOptionsCard>
          </ShowcaseItem>
        </div>
      </section>
    </section>
  );
}
