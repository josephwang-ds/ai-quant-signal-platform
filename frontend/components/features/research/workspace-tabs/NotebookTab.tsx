"use client";

import ErrorAlert from "@/components/ui/ErrorAlert";
import ResearchNotebook from "@/components/features/research/notebook/ResearchNotebook";
import ResearchTimeline from "@/components/features/research/ResearchTimeline";
import ResearchCopilotPanel from "@/components/features/research/copilot/ResearchCopilotPanel";
import type { Language, TranslationKey } from "@/lib/i18n";
import type { ResearchDetail, ResearchWorkspaceSection } from "@/types/research";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";
import type { ResearchCopilotRequestStatus, ResearchCopilotResult } from "@/types/researchCopilot";
import type { ResearchValidationStatus } from "@/types/researchValidation";
import type { ResearchEvaluationResult, ResearchEvaluationRequestStatus } from "@/types/researchEvaluation";
import EvaluationBlock from "./EvaluationBlock";

export type NotebookTabProps = {
  section: Extract<ResearchWorkspaceSection, "notebook" | "timeline" | "copilot">;
  researchId: string;
  language: Language;
  tr: (key: TranslationKey) => string;
  displayResearch: ResearchDetail;
  sessionNotebookEntries: NotebookEntry[];
  handleSessionEntrySaved: (entry: NotebookEntry, timelineEvent: ResearchTimelineEvent) => void;
  timelineEvents: ResearchTimelineEvent[];
  copilotEnabled: boolean;
  copilotStatus: ResearchCopilotRequestStatus;
  copilotResult: ResearchCopilotResult | null;
  copilotError: string | null;
  copilotQuestion: string;
  setCopilotQuestion: (value: string) => void;
  askCopilot: (question: string) => void | Promise<void>;
  copilotSampleQuestions: string[];
  validationEvidenceActive: boolean;
  validationStatus: ResearchValidationStatus;
  validationError: string | null;
  evaluationEnabled: boolean;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  evaluationError: string | null;
  reloadEvaluation: () => void;
};

export default function NotebookTab(props: NotebookTabProps) {
  const {
    section,
    researchId,
    language,
    tr,
    displayResearch,
    sessionNotebookEntries,
    handleSessionEntrySaved,
    timelineEvents,
    copilotEnabled,
    copilotStatus,
    copilotResult,
    copilotError,
    copilotQuestion,
    setCopilotQuestion,
    askCopilot,
    copilotSampleQuestions,
    validationEvidenceActive,
    validationStatus,
    validationError,
    evaluationEnabled,
    evaluationStatus,
    evaluation,
    evaluationError,
    reloadEvaluation,
  } = props;

  if (section === "notebook") {
    return (
      <ResearchNotebook
        research={displayResearch}
        language={language}
        sessionEntries={sessionNotebookEntries}
        onSessionEntrySaved={handleSessionEntrySaved}
        labels={{
          title: tr("researchNbDesignNotesTitle"),
          entryCount: tr("researchNbEntryCount"),
          lastUpdated: tr("researchNbLastUpdated"),
          newEntry: tr("researchNbNewEntry"),
          loading: tr("researchNbLoading"),
          errorTitle: tr("researchNbErrorTitle"),
          retry: tr("researchNbRetry"),
          emptyTitle: tr("researchNbEmptyTitle"),
          emptyDescription: tr("researchNbEmptyDescription"),
          filterEmptyTitle: tr("researchNbFilterEmptyTitle"),
          filterEmptyDescription: tr("researchNbFilterEmptyDescription"),
          filters: {
            filterType: tr("researchNbFilterType"),
            filterAll: tr("researchNbFilterAll"),
            sort: tr("researchNbSort"),
            sortNewest: tr("researchNbSortNewest"),
            sortOldest: tr("researchNbSortOldest"),
          },
          card: {
            author: tr("researchNbCardAuthor"),
            created: tr("researchNbCardCreated"),
            edited: tr("researchNbCardEdited"),
            related: tr("researchNbCardRelated"),
            tags: tr("researchWsTags"),
          },
          composer: {
            title: tr("researchNbComposerTitle"),
            entryType: tr("researchNbComposerType"),
            entryTitle: tr("researchNbComposerEntryTitle"),
            content: tr("researchNbComposerContent"),
            tags: tr("researchNbComposerTags"),
            tagsHint: tr("researchNbComposerTagsHint"),
            relatedArtifact: tr("researchNbComposerArtifact"),
            relatedNone: tr("researchNbComposerArtifactNone"),
            save: tr("researchNbComposerSave"),
            cancel: tr("researchNbComposerCancel"),
            entryTypeRequired: tr("researchNbValidationType"),
            titleRequired: tr("researchNbValidationTitle"),
            bodyRequired: tr("researchNbValidationBody"),
          },
        }}
      />
    );

  }

  if (section === "timeline") {
    return (
      <ResearchTimeline
        events={timelineEvents}
        language={language}
        labels={{
          title: tr("researchTlTitle"),
          description: tr("researchTlDescription"),
          sessionNote: tr("researchTlSessionNote"),
          empty: tr("researchTlEmpty"),
        }}
      />
    );

  }

  if (section === "copilot") {
    if (!copilotEnabled) {
      return (
        <ErrorAlert
          title={tr("researchCopilotUnavailableTitle")}
          message={tr("researchCopilotUnavailableDescription")}
        />
      );
    }

    return (
      <div className="research-review-copilot">
        <EvaluationBlock
            researchId={researchId}
            language={language}
            tr={tr}
            evaluationEnabled={evaluationEnabled}
            evaluationStatus={evaluationStatus}
            evaluation={evaluation}
            evaluationError={evaluationError}
            reloadEvaluation={reloadEvaluation}
          />
        <ResearchCopilotPanel
          labels={{
            title: tr("researchCopilotTitle"),
            subtitle: tr("researchCopilotSubtitle"),
            disclaimer: tr("researchCopilotDisclaimer"),
            sampleQuestionsTitle: tr(
              "researchCopilotSampleQuestionsTitle"
            ),
            questionPlaceholder: tr("researchCopilotQuestionPlaceholder"),
            askButton: tr("researchCopilotAskButton"),
            askingButton: tr("researchCopilotAskingButton"),
            answerTitle: tr("researchCopilotAnswerTitle"),
            citationsTitle: tr("researchCopilotCitationsTitle"),
            warningsTitle: tr("researchCopilotWarningsTitle"),
            groundingTitle: tr("researchCopilotGroundingTitle"),
            generatedAt: tr("researchCopilotGeneratedAt"),
            grounded: tr("researchCopilotGrounded"),
            partiallyGrounded: tr("researchCopilotPartiallyGrounded"),
            unavailable: tr("researchCopilotUnavailable"),
            awaitingValidationTitle: tr("researchCopilotAwaitingValidationTitle"),
            awaitingValidationDescription: tr(
              "researchCopilotAwaitingValidationDescription"
            ),
            goToValidation: tr("researchCopilotGoToValidation"),
            notConfigured: tr("researchCopilotNotConfigured"),
            limitations: tr("researchCopilotLimitations"),
          }}
          sampleQuestions={copilotSampleQuestions}
          status={
            validationEvidenceActive && validationStatus === "loading"
              ? "loading"
              : copilotStatus
          }
          result={copilotResult}
          error={
            copilotError ??
            (validationEvidenceActive && validationStatus === "error"
              ? validationError
              : null)
          }
          question={copilotQuestion}
          onQuestionChange={setCopilotQuestion}
          onAsk={() => void askCopilot(copilotQuestion)}
          onSampleQuestion={(sample) => {
            setCopilotQuestion(sample);
            void askCopilot(sample);
          }}
          onGoToValidation={() => {
            window.location.href = `/research/${encodeURIComponent(researchId)}?tab=validation`;
          }}
        />
      </div>
    );

  }

  return null;
}
