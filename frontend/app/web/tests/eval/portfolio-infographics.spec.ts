import { test } from "@playwright/test";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

// 포트폴리오용 인포그래픽(에이전트 흐름도) 렌더링.
// 원본은 _workspace/portfolio-screenshots/infographics/infographics.source.html 이며,
// 문구를 고친 뒤 이 스펙을 다시 돌리면 PNG가 갱신된다.
const infographicDir = resolve(__dirname, "../../../../_workspace/portfolio-screenshots/infographics");
const sourcePage = pathToFileURL(resolve(infographicDir, "infographics.source.html")).href;
// 발표 슬라이드 좌측 열(폰 스크린샷 옆)에 넣는 세로 압축 버전.
const compactPage = pathToFileURL(resolve(infographicDir, "infographics-compact.source.html")).href;

const boards = [
  { id: "shopping", file: "infographic-shopping-agent", url: sourcePage },
  { id: "hospital", file: "infographic-hospital-recommendation", url: sourcePage },
  { id: "shopping-compact", file: "infographic-shopping-agent-compact", url: compactPage },
  { id: "hospital-compact", file: "infographic-hospital-recommendation-compact", url: compactPage },
];

test.use({ viewport: { width: 1000, height: 900 }, deviceScaleFactor: 2 });

test.describe("portfolio infographics", () => {
  for (const board of boards) {
    test(`render ${board.id} infographic`, async ({ page }) => {
      await page.goto(board.url);
      await page.locator(`#${board.id}`).screenshot({ path: resolve(infographicDir, `${board.file}.png`) });
    });
  }
});
