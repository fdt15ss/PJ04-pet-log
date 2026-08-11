import { expect, test, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { installMockPetLogApi } from "../support/mock-api";

const outputDir = resolve(__dirname, "../../../../_workspace/portfolio-screenshots/agent-before-after");
// AppShell이 h-dvh + 내부 스크롤 구조라 fullPage 캡처가 뷰포트 높이로 잘린다.
// 실행 전/후 대비가 한 장에 담기도록 화면 높이를 늘려서 캡처한다.
const shoppingViewport = { width: 390, height: 1560 };
const hospitalViewport = { width: 390, height: 1960 };

const hospitalRecords = [
  {
    id: "record-hospital-01",
    time: "21:40",
    date: "5월 14일",
    recordedAt: "2026-05-14T12:40:00.000Z",
    category: "behavior" as const,
    categoryChoice: "behavior" as const,
    title: "산책 중 자주 멈춤",
    detail: "산책 중 다리를 절며 자주 멈추고 계단을 오르지 않으려 했어요.",
    status: "alert" as const,
    structured: {
      sourceText: "산책 중 다리를 절며 자주 멈추고 계단을 오르지 않으려 했어요.",
      normalizedSummary: "산책 중 파행 및 계단 회피",
      suggestedCategory: "behavior" as const,
      detectedCategories: ["behavior"],
      confidence: 0.88,
      measurements: [],
      needsConfirmation: false,
    },
  },
  {
    id: "record-hospital-02",
    time: "08:20",
    date: "5월 14일",
    recordedAt: "2026-05-14T00:20:00.000Z",
    category: "stool" as const,
    categoryChoice: "stool" as const,
    title: "무른 변 확인",
    detail: "아침 배변이 평소보다 무르고 횟수가 3회로 늘었어요.",
    status: "alert" as const,
    structured: {
      sourceText: "아침 배변이 평소보다 무르고 횟수가 3회로 늘었어요.",
      normalizedSummary: "무른 변 3회",
      suggestedCategory: "stool" as const,
      detectedCategories: ["stool"],
      confidence: 0.92,
      measurements: [{ label: "배변", value: "3회" }],
      needsConfirmation: false,
    },
  },
  {
    id: "record-hospital-03",
    time: "19:05",
    date: "5월 13일",
    recordedAt: "2026-05-13T10:05:00.000Z",
    category: "meal" as const,
    categoryChoice: "meal" as const,
    title: "저녁 사료 절반 남김",
    detail: "저녁 사료 40g 중 절반만 먹고 물을 평소보다 많이 마셨어요.",
    status: "notice" as const,
    structured: {
      sourceText: "저녁 사료 40g 중 절반만 먹고 물을 평소보다 많이 마셨어요.",
      normalizedSummary: "사료 20g 섭취, 음수량 증가",
      suggestedCategory: "meal" as const,
      detectedCategories: ["meal"],
      confidence: 0.9,
      measurements: [{ label: "사료", value: "20g" }],
      needsConfirmation: false,
    },
  },
];

const shoppingAgentResult = [
  {
    id: "shopping-agent-01",
    category: "사료" as const,
    title: "관절 케어 소형견 사료 1.2kg",
    detail: "글루코사민·MSM 강화 배합으로 소형견 관절 부담을 줄인 주식 사료입니다.",
    reason: "최근 3일 산책 기록에서 파행과 계단 회피가 반복되어 관절 케어 성분 사료를 우선 추천했습니다.",
    tone: "green" as const,
    mall_name: "네이버쇼핑",
    lowest_price: 28900,
    product_url: "https://example.com/product/joint-care-food",
    query: "소형견 관절 사료",
    source_record_ids: ["record-hospital-01"],
  },
  {
    id: "shopping-agent-02",
    category: "건강 용품" as const,
    title: "반려견 장 건강 유산균 30포",
    detail: "무른 변이 반복될 때 급여하는 반려견 전용 프로바이오틱스 분말입니다.",
    reason: "배변 기록에서 무른 변이 3회로 늘어난 패턴이 감지되어 장 건강 보조제를 추천했습니다.",
    tone: "orange" as const,
    mall_name: "쿠팡",
    lowest_price: 19800,
    product_url: "https://example.com/product/probiotics",
    query: "강아지 유산균",
    source_record_ids: ["record-hospital-02"],
  },
  {
    id: "shopping-agent-03",
    category: "케어 용품" as const,
    title: "미끄럼 방지 러그 100x150",
    detail: "거실 바닥 미끄러짐을 줄여 관절 충격을 완화하는 논슬립 매트입니다.",
    reason: "관절 주의 기록과 실내 활동 기록을 함께 반영해 생활 환경 개선 용품을 함께 제안했습니다.",
    tone: "blue" as const,
    mall_name: "11번가",
    lowest_price: 34500,
    product_url: "https://example.com/product/non-slip-rug",
    query: "강아지 미끄럼 방지 매트",
    source_record_ids: ["record-hospital-01"],
  },
];

const hospitalAgentResponse = {
  current_time: "2026-05-15T10:30:00+09:00",
  search_center: {
    latitude: 37.5013,
    longitude: 127.0396,
    radius_meters: 3000,
    location_source: "device_gps",
    accuracy_meters: 32,
    emergency_mode: false,
  },
  recommendations: [
    {
      place_id: "hospital-agent-01",
      name: "강남 24시 동물메디컬센터",
      address: "서울 강남구 테헤란로 132",
      phone_number: "02-000-0001",
      google_maps_url: "https://maps.google.com/?q=hospital-agent-01",
      latitude: 37.5024,
      longitude: 127.0371,
      rating: 4.7,
      user_rating_count: 812,
      is_open_now: true,
      is_24_hours: true,
      weekday_text: [],
      distance_meters: 420,
      reason: "야간 진료가 가능하고 정형외과 진료 항목을 운영합니다.",
    },
    {
      place_id: "hospital-agent-02",
      name: "역삼 정형외과 동물병원",
      address: "서울 강남구 역삼로 210",
      phone_number: "02-000-0002",
      google_maps_url: "https://maps.google.com/?q=hospital-agent-02",
      latitude: 37.4998,
      longitude: 127.0432,
      rating: 4.5,
      user_rating_count: 361,
      is_open_now: true,
      is_24_hours: false,
      weekday_text: [],
      distance_meters: 780,
      reason: "관절·파행 증상 진료 이력이 많은 병원입니다.",
    },
    {
      place_id: "hospital-agent-03",
      name: "삼성동 반려동물 종합병원",
      address: "서울 강남구 봉은사로 512",
      phone_number: "02-000-0003",
      google_maps_url: "https://maps.google.com/?q=hospital-agent-03",
      latitude: 37.5089,
      longitude: 127.0512,
      rating: 4.3,
      user_rating_count: 224,
      is_open_now: false,
      is_24_hours: false,
      weekday_text: [],
      distance_meters: 1640,
      reason: "내과 검진과 소화기 진료를 함께 볼 수 있습니다.",
    },
  ],
};

function ok(data: unknown) {
  return {
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ ok: true, data }),
  };
}

// 확장 상태(쇼핑 저장/필터, 병원 메모·위치)는 PUT /expansion-state 응답으로 확정되므로
// 목 응답이 없으면 UI 상태가 되돌아간다.
async function mockExpansionStatePersistence(page: Page) {
  await page.route(/\/api\/v1\/expansion-state/, async (route) => {
    if (route.request().method() !== "PUT") {
      await route.fallback();
      return;
    }

    await route.fulfill(ok({ expansionState: route.request().postDataJSON() }));
  });
}

async function shot(page: Page, name: string) {
  await page.screenshot({ path: resolve(outputDir, `${name}.png`), fullPage: true });
}

test.beforeAll(() => {
  mkdirSync(outputDir, { recursive: true });
});

test.describe("agent before/after portfolio screenshots", () => {
  test("shopping agent before and after", async ({ page }) => {
    await page.setViewportSize(shoppingViewport);
    await installMockPetLogApi(page, hospitalRecords);
    await mockExpansionStatePersistence(page);

    let releaseAgent = () => {};
    const agentDone = new Promise<void>((resolve) => {
      releaseAgent = resolve;
    });

    await page.route(/\/api\/v1\/shopping\/recommendations/, async (route) => {
      await agentDone;
      await route.fulfill(ok({ recommendations: shoppingAgentResult }));
    });

    await page.goto("/shopping");

    // 실행 전: LangGraph 쇼핑 추천 에이전트 호출 중 (동기화 로딩 상태)
    await expect(page.locator("body")).toContainText("상품 추천 동기화 중");
    await page.waitForTimeout(400);
    await shot(page, "01-shopping-agent-before");

    // 실행 후: 에이전트가 반환한 상품 카드
    releaseAgent();
    await expect(page.locator("body")).toContainText("관절 케어 소형견 사료 1.2kg");
    await expect(page.locator("body")).not.toContainText("상품 추천 동기화 중");
    await page.waitForTimeout(400);
    await shot(page, "02-shopping-agent-after");

    // 추천 이유 펼침: 기록 근거 노출
    await page.getByRole("button", { name: "추천 이유 보기" }).first().click();
    await expect(page.locator("body")).toContainText("최근 3일 산책 기록에서");
    await page.waitForTimeout(300);
    await shot(page, "03-shopping-agent-after-reason");
  });

  test("hospital agent before and after", async ({ page, context }) => {
    await page.setViewportSize(hospitalViewport);
    await installMockPetLogApi(page, hospitalRecords);
    await mockExpansionStatePersistence(page);

    let releaseAgent = () => {};
    const agentDone = new Promise<void>((resolve) => {
      releaseAgent = resolve;
    });

    await page.route(/\/api\/v1\/hospitals\/recommendations/, async (route) => {
      await agentDone;
      await route.fulfill(ok(hospitalAgentResponse));
    });

    await context.grantPermissions(["geolocation"]);
    await context.setGeolocation({ latitude: 37.5013, longitude: 127.0396 });

    await page.goto("/hospital");
    await expect(page.locator("body")).toContainText("근처 동물병원");

    // 증상 메모 입력 (병원 추천 요청 컨텍스트)
    await page.getByPlaceholder("예:").fill("어제부터 산책 중 다리를 절며 자주 멈추고, 아침 배변이 무릅니다.");
    await page.waitForTimeout(300);

    // 실행 전: 위치 미적용 · 병원 추천 요청 전 상태
    await shot(page, "04-hospital-agent-before");

    await page.getByRole("button", { name: "내 위치 찾기" }).click();
    await expect(page.locator("body")).toContainText("병원 정보를 불러오는 중...");
    await page.waitForTimeout(300);
    await shot(page, "05-hospital-agent-loading");

    // 실행 후: 위치 기반 병원 추천 결과
    releaseAgent();
    await expect(page.locator("body")).toContainText("강남 24시 동물메디컬센터");
    await expect(page.locator("body")).toContainText("내 위치 적용됨");
    await page.waitForTimeout(500);
    await shot(page, "06-hospital-agent-after");

    // 병원 선택 후 상담 준비 상태
    await page.getByRole("button", { name: /강남 24시 동물메디컬센터/ }).click();
    await expect(page.locator("body")).toContainText("선택됨");
    await page.waitForTimeout(300);
    await shot(page, "07-hospital-agent-after-selected");
  });
});
