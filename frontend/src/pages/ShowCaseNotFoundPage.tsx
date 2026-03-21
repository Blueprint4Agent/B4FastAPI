import { useNavigate } from "react-router-dom";

import { Button, PanelCard } from "../components/ui";

export function ShowCaseNotFoundPage() {
    const navigate = useNavigate();

    return (
        <section className="page-content">
            <PanelCard
                title="404 Not Found"
                subtitle="The page you are looking for does not exist."
            >
                <div className="showcase-not-found__actions">
                    <Button type="button" onClick={() => navigate("/show-case", { replace: true })}>
                        Back to Main Page
                    </Button>
                </div>
            </PanelCard>
        </section>
    );
}
