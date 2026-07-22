"use client";

import type { Dispatch, ReactNode, SetStateAction } from "react";
import ResearchExperiments from "@/components/features/research/experiments/ResearchExperiments";
import ResearchValidationPanel from "@/components/features/research/validation/ResearchValidationPanel";
import ResearchRobustnessCenter from "@/components/features/research/robustness/ResearchRobustnessCenter";
import Button from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import { buildRobustnessCenterLabels } from "@/lib/robustnessCenterLabels";
import type { Language, TranslationKey } from "@/lib/i18n";
import type { ResearchExperiment } from "@/types/experiment";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";
import type { ResearchDetail, ResearchWorkspaceSection } from "@/types/research";
import type { ResearchValidationResult, ResearchValidationStatus } from "@/types/researchValidation";
import type { ResearchEvaluationResult, ResearchEvaluationRequestStatus } from "@/types/researchEvaluation";
import EvaluationBlock from "./EvaluationBlock";

export type EvidenceTabProps = {
  section: Extract<ResearchWorkspaceSection, "experiments" | "validation" | "evaluation" | "robustness">;
  researchId: string;
  language: Language;
  tr: (key: TranslationKey) => string;
  displayResearch: ResearchDetail;
  provenanceSlot: ReactNode;
  navigateToSection: (section: ResearchWorkspaceSection) => void;
  sessionExperiments: ResearchExperiment[];
  selectedExperimentId: string | null;
  setSelectedExperimentId: Dispatch<SetStateAction<string | null>>;
  handleExperimentDesigned: (payload: {
    experiment: ResearchExperiment;
    notebookEntry: NotebookEntry;
    timelineEvent: ResearchTimelineEvent;
  }) => void;
  executedExperiments: ResearchExperiment[] | null;
  validationEnabled: boolean;
  validationStatus: ResearchValidationStatus;
  validation: ResearchValidationResult | null;
  validationError: string | null;
  reloadValidation: () => void;
  evaluationEnabled: boolean;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  evaluationError: string | null;
  reloadEvaluation: () => void;
};

export default function EvidenceTab(props: EvidenceTabProps) {
  const {
    section,
    researchId,
    language,
    tr,
    displayResearch,
    provenanceSlot,
    navigateToSection,
    sessionExperiments,
    selectedExperimentId,
    setSelectedExperimentId,
    handleExperimentDesigned,
    executedExperiments,
    validationEnabled,
    validationStatus,
    validation,
    validationError,
    reloadValidation,
    evaluationEnabled,
    evaluationStatus,
    evaluation,
    evaluationError,
    reloadEvaluation,
  } = props;

  if (section === "experiments") {
    return (
      <ResearchExperiments
        research={displayResearch}
        language={language}
        sessionExperiments={sessionExperiments}
        selectedExperimentId={selectedExperimentId}
        onSelectExperiment={setSelectedExperimentId}
        onExperimentDesigned={handleExperimentDesigned}
        executedExperiments={executedExperiments}
        provenanceSlot={provenanceSlot}
        labels={{
          title: tr("researchExpTitle"),
          totalCount: tr("researchExpTotalCount"),
          activeCount: tr("researchExpActiveCount"),
          newExperiment: tr("researchExpNew"),
          loading: tr("researchExpLoading"),
          errorTitle: tr("researchExpErrorTitle"),
          retry: tr("researchExpRetry"),
          emptyTitle: tr("researchExpEmptyTitle"),
          emptyDescription: tr("researchExpEmptyDescription"),
          filterEmptyTitle: tr("researchExpFilterEmptyTitle"),
          filterEmptyDescription: tr("researchExpFilterEmptyDescription"),
          notFoundTitle: tr("researchExpNotFoundTitle"),
          notFoundDescription: tr("researchExpNotFoundDescription"),
          backToList: tr("researchExpBackToList"),
          filters: {
            search: tr("researchExpSearch"),
            searchPlaceholder: tr("researchExpSearchPlaceholder"),
            status: tr("researchExpFilterStatus"),
            type: tr("researchExpFilterType"),
            sort: tr("researchExpSort"),
            all: tr("researchExpFilterAll"),
            sortUpdated: tr("researchExpSortUpdated"),
            sortCreated: tr("researchExpSortCreated"),
            sortResult: tr("researchExpSortResult"),
          },
          card: {
            hypothesis: tr("researchExpCardHypothesis"),
            dataset: tr("researchExpCardDataset"),
            window: tr("researchExpCardWindow"),
            benchmark: tr("researchExpCardBenchmark"),
            owner: tr("researchListOwner"),
            updated: tr("researchListUpdated"),
            result: tr("researchExpCardResult"),
            readiness: tr("researchExpCardReadiness"),
            parameters: tr("researchExpCardParameters"),
            linkedNotes: tr("researchExpCardLinkedNotes"),
            openDetail: tr("researchExpOpenDetail"),
            sharpe: tr("researchExpMetricSharpe"),
            maxDrawdown: tr("researchExpMetricMaxDD"),
          },
          composer: {
            title: tr("researchExpComposerTitle"),
            name: tr("researchExpComposerName"),
            hypothesis: tr("researchExpComposerHypothesis"),
            experimentType: tr("researchExpComposerType"),
            dataset: tr("researchExpComposerDataset"),
            startDate: tr("researchExpComposerStart"),
            endDate: tr("researchExpComposerEnd"),
            benchmark: tr("researchExpComposerBenchmark"),
            parameters: tr("researchExpComposerParameters"),
            parametersHint: tr("researchExpComposerParametersHint"),
            successCriteria: tr("researchExpComposerSuccess"),
            falsification: tr("researchExpComposerFalsify"),
            notes: tr("researchExpComposerNotes"),
            save: tr("researchExpComposerSave"),
            cancel: tr("researchExpComposerCancel"),
            nameRequired: tr("researchExpValidationName"),
            hypothesisRequired: tr("researchExpValidationHypothesis"),
            typeRequired: tr("researchExpValidationType"),
            datasetRequired: tr("researchExpValidationDataset"),
            startRequired: tr("researchExpValidationStart"),
            endRequired: tr("researchExpValidationEnd"),
            dateRangeInvalid: tr("researchExpValidationDateRange"),
            successRequired: tr("researchExpValidationSuccess"),
            falsificationRequired: tr("researchExpValidationFalsify"),
          },
          detail: {
            title: tr("researchExpDetailTitle"),
            close: tr("researchExpDetailClose"),
            overview: tr("researchExpDetailOverview"),
            hypothesis: tr("researchExpCardHypothesis"),
            configuration: tr("researchExpDetailConfig"),
            parameters: tr("researchExpCardParameters"),
            results: tr("researchExpCardResult"),
            notes: tr("researchExpComposerNotes"),
            relatedEvidence: tr("researchExpDetailEvidence"),
            linkedNotebook: tr("researchExpDetailNotebook"),
            validationReadiness: tr("researchExpCardReadiness"),
            dataset: tr("researchExpCardDataset"),
            window: tr("researchExpCardWindow"),
            benchmark: tr("researchExpCardBenchmark"),
            owner: tr("researchListOwner"),
            created: tr("researchWsCreated"),
            updated: tr("researchListUpdated"),
            success: tr("researchExpComposerSuccess"),
            falsification: tr("researchExpComposerFalsify"),
            none: tr("researchExpNone"),
            lifecycle: {
              title: tr("researchExpLifecycleTitle"),
              description: tr("researchExpLifecycleDescription"),
              completed: tr("researchExpLifecycleCompleted"),
              current: tr("researchExpLifecycleCurrent"),
              upcoming: tr("researchExpLifecycleUpcoming"),
              terminalNote: tr("researchExpLifecycleTerminal"),
              governedNote: tr("researchExpLifecycleGoverned"),
            },
            metrics: {
              title: tr("researchExpMetricsTitle"),
              disclaimer: tr("researchExpMetricsDisclaimer"),
              sharpe: tr("researchExpMetricSharpe"),
              cagr: tr("researchExpMetricCagr"),
              maxDrawdown: tr("researchExpMetricMaxDD"),
              volatility: tr("researchExpMetricVol"),
              tradeCount: tr("researchExpMetricTrades"),
              winRate: tr("researchExpMetricWinRate"),
              totalTransactionCost: tr("researchExpMetricCost"),
            },
          },
        }}
      />
    );

  }

  if (section === "validation") {
    let validationBlock: ReactNode = null;
    if (!validationEnabled) {
      validationBlock = (
        <ErrorAlert
          title={tr("researchValUnavailableTitle")}
          message={tr("researchValUnavailableDescription")}
        />
      );
    } else if (validationStatus === "loading") {
      validationBlock = <LoadingState message={tr("researchValLoading")} />;
    } else if (validationStatus === "error") {
      validationBlock = (
        <div className="research-execution-error">
          <ErrorAlert
            title={tr("researchValUnavailableTitle")}
            message={validationError ?? tr("researchValUnavailableDescription")}
          />
          <Button primary onClick={reloadValidation}>
            {tr("researchValRetry")}
          </Button>
        </div>
      );
    } else if (validationStatus === "ready" && validation) {
      validationBlock = (
        <ResearchValidationPanel
          validation={validation}
          language={language}
          labels={{
          title: tr("researchWsValidationTitle"),
          summary: tr("researchValSummary"),
          status: tr("researchValStatus"),
          evidenceComplete: tr("researchValEvidenceComplete"),
          yes: tr("researchValYes"),
          no: tr("researchValNo"),
          completed: tr("researchWsValidationCompleted"),
          incomplete: tr("researchValIncomplete"),
          failed: tr("researchValFailed"),
          unavailable: tr("researchValUnavailable"),
          source: tr("researchValSource"),
          generated: tr("researchValGenerated"),
          rules: tr("researchValRules"),
          warnings: tr("researchValWarnings"),
          dataNotes: tr("researchValDataNotes"),
          blockers: tr("researchValBlockers"),
          evidence: tr("researchValEvidence"),
          oosTitle: tr("researchValOosTitle"),
          splitDate: tr("researchValSplitDate"),
          inSampleRatio: tr("researchValInSampleRatio"),
          minimumOos: tr("researchValMinimumOos"),
          boundary: tr("researchValBoundary"),
          inSample: tr("researchValInSample"),
          outOfSample: tr("researchValOutOfSample"),
          benchmark: tr("researchValBenchmark"),
          observations: tr("researchValObservations"),
          metric: tr("researchValMetric"),
          totalReturn: tr("researchValTotalReturn"),
          cagr: tr("researchValCagr"),
          sharpe: tr("researchValSharpe"),
          maxDrawdown: tr("researchValMaxDrawdown"),
          volatility: tr("researchValVolatility"),
          trades: tr("researchValTrades"),
          totalCosts: tr("researchValTotalCosts"),
          parameterTitle: tr("researchValParameterTitle"),
          validCombinations: tr("researchValValidCombinations"),
          profitableCombinations: tr("researchValProfitableCombinations"),
          positiveSharpe: tr("researchValPositiveSharpe"),
          medianSharpe: tr("researchValMedianSharpe"),
          sharpeRange: tr("researchValSharpeRange"),
          medianDrawdown: tr("researchValMedianDrawdown"),
          canonicalPercentile: tr("researchValCanonicalPercentile"),
          shortWindow: tr("researchValShortWindow"),
          longWindow: tr("researchValLongWindow"),
          canonical: tr("researchValCanonical"),
          costTitle: tr("researchValCostTitle"),
          transactionCost: tr("researchValTransactionCost"),
          returnDegradation: tr("researchValReturnDegradation"),
          sharpeDegradation: tr("researchValSharpeDegradation"),
          mathematicallyValid: tr("researchValMathematicallyValid"),
          canonicalCost: tr("researchValCanonicalCost"),
          dataQualityTitle: tr("researchValDataQualityTitle"),
          provider: tr("researchValProvider"),
          dateRange: tr("researchValDateRange"),
          cache: tr("researchValCache"),
          cacheHit: tr("researchValCacheHit"),
          cacheMiss: tr("researchValCacheMiss"),
          fatalIssues: tr("researchValFatalIssues"),
          checks: tr("researchValChecks"),
          check: tr("researchValCheck"),
          severity: tr("researchValSeverity"),
          details: tr("researchValDetails"),
          notAvailable: tr("researchValNotAvailable"),
        }}
        />
      );
    }

    return (
      <>
        {validationBlock}
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
      </>
    );

  }

  if (section === "evaluation") {
    return (<EvaluationBlock
        researchId={researchId}
        language={language}
        tr={tr}
        evaluationEnabled={evaluationEnabled}
        evaluationStatus={evaluationStatus}
        evaluation={evaluation}
        evaluationError={evaluationError}
        reloadEvaluation={reloadEvaluation}
      />);;
  }

  if (section === "robustness") {
    const evaluationReadyForRobustness =
      evaluationStatus === "ready" ? evaluation : null;
    const validationReadyForRobustness =
      validationStatus === "ready" ? validation : null;

    return (
      <ResearchRobustnessCenter
        validation={validationReadyForRobustness}
        evaluation={evaluationReadyForRobustness}
        labels={buildRobustnessCenterLabels(tr)}
        onContinue={() => navigateToSection("paper")}
      />
    );

  }

  return null;
}
