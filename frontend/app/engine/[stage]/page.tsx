import { notFound } from "next/navigation";
import ResearchEngineStagePage from "@/components/features/platform/ResearchEngineStagePage";
import {
  ENGINE_STAGES,
  type EngineStageId,
} from "@/lib/platformArchitecture";

type Props = {
  params: Promise<{ stage: string }>;
};

export function generateStaticParams() {
  return ENGINE_STAGES.map((stage) => ({ stage: stage.id }));
}

export default async function EngineStageRoutePage({ params }: Props) {
  const { stage } = await params;
  const valid = ENGINE_STAGES.some((item) => item.id === stage);
  if (!valid) {
    notFound();
  }
  return <ResearchEngineStagePage stageId={stage as EngineStageId} />;
}
