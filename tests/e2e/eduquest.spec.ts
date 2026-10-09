import { expect, test } from '@playwright/test';

const baseURL = process.env.BASE_URL ?? 'http://localhost:3000';
const facultyCard = /Faculty Full Access/;
const adminCard = /Administrator System Control/;

test.describe('EduQuest dashboard smoke tests', () => {
  test('invalid administrator credentials show an inline error', async ({ page }) => {
    await page.route('**/api/admin/login', (route) =>
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Invalid credentials' }),
      }),
    );

    await page.goto(baseURL);
    await page.getByRole('button', { name: adminCard }).click();
    await page.getByLabel('Email address').fill('admin@example.test');
    await page.getByLabel('Password').fill('incorrect-password');
    await page.getByRole('button', { name: /Sign in to Administrator Dashboard/ }).click();

    await expect(page.getByText('Invalid credentials', { exact: true })).toBeVisible();
    await expect(page).toHaveURL(baseURL + '/');
  });

  test('valid faculty credentials navigate to the faculty dashboard', async ({ page }) => {
    await page.route('**/api/faculty/login', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, token: 'playwright-test-token' }),
      }),
    );

    await page.goto(baseURL);
    await page.getByRole('button', { name: facultyCard }).click();
    await page.getByLabel('Email address').fill('faculty@example.test');
    await page.getByLabel('Password').fill('valid-test-password');
    await page.getByRole('button', { name: /Sign in to Faculty Dashboard/ }).click();

    await expect(page).toHaveURL(baseURL + '/faculty-dashboard');
    await expect(page.getByRole('heading', { name: 'Faculty Dashboard' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Switch to dark mode' })).toBeVisible();
  });

  test('theme toggle persists through a page reload', async ({ page }) => {
    await page.goto(baseURL);
    await page.getByRole('button', { name: 'Switch to dark mode' }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page.getByRole('button', { name: 'Switch to light mode' })).toHaveAttribute('aria-pressed', 'true');

    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page.getByRole('button', { name: 'Switch to light mode' })).toBeVisible();
  });

  test('generated papers are reviewed before a download is available', async ({ page }) => {
    let reviewedText: string | undefined;
    await page.route('**/api/generate-question-paper', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          paper_information: {
            subject: 'Data Structures',
            subject_code: 'DS',
            branch: 'CSE',
            semester: 4,
            exam_type: 'University',
            paper_total_marks: 70,
          },
          sections: {
            Q1: {
              questions_to_attempt: 5,
              questions: [{
                canonical_id: 'question-1',
                question_text: 'Explain binary search trees.',
                unit: 'Unit-I',
                marks: 2,
                rua: 'U',
                difficulty: 'Easy',
                course_outcome: 'CO1',
              }],
            },
          },
        }),
      }),
    );
    await page.route('**/api/download-reviewed-paper', async (route) => {
      reviewedText = route.request().postDataJSON().sections.Q1.questions[0].question_text;
      await route.fulfill({
        status: 200,
        contentType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        body: 'reviewed-docx',
      });
    });

    await page.goto(baseURL);
    await page.evaluate(() => {
      sessionStorage.setItem('facultyAuthenticated', 'true');
      sessionStorage.setItem('authToken', 'playwright-faculty-token');
    });
    await page.goto(`${baseURL}/faculty-dashboard`);
    await page.getByRole('button', { name: 'Paper Generation', exact: true }).click();
    const automaticDownload = page.waitForEvent('download', { timeout: 1500 })
      .then(() => true)
      .catch(() => false);
    await page.getByRole('button', { name: 'Generate question paper' }).click();

    await expect(page.getByText('Review Generated Paper', { exact: true })).toBeVisible();
    const questionEditor = page.getByRole('textbox', { name: 'Edit Q1 question 1' });
    await expect(questionEditor).toHaveValue('Explain binary search trees.');
    await expect(page.getByRole('button', { name: 'Approve and download' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Generate question paper' })).toHaveCount(0);
    expect(await automaticDownload).toBe(false);

    await questionEditor.fill('Explain a balanced binary search tree.');
    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Approve and download' }).click();
    expect((await download).suggestedFilename()).toBe('Data_Structures_Question_Paper.docx');
    expect(reviewedText).toBe('Explain a balanced binary search tree.');
  });

  test('Advance Java generation sends its registered subject code', async ({ page }) => {
    let generationPayload: Record<string, unknown> | undefined;
    await page.route('**/api/paper-generation/subjects', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          subjects: [{
            subject_id: 1,
            subject_name: 'Advance Java',
            subject_code: '21526',
            branch: 'Computer Engineering',
            semester: '5',
          }],
        }),
      }),
    );
    await page.route('**/api/generate-question-paper', async (route) => {
      generationPayload = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          paper_information: {
            subject: 'Advance Java',
            subject_code: '21526',
            branch: 'Computer Engineering',
            semester: 5,
            exam_type: 'University',
            paper_total_marks: 70,
          },
          sections: {
            Q1: { questions_to_attempt: 5, questions: [] },
          },
        }),
      });
    });

    await page.goto(baseURL);
    await page.evaluate(() => {
      sessionStorage.setItem('facultyAuthenticated', 'true');
      sessionStorage.setItem('authToken', 'playwright-faculty-token');
    });
    await page.goto(`${baseURL}/faculty-dashboard`);
    await page.getByRole('button', { name: 'Paper Generation', exact: true }).click();
    await page.getByLabel('Semester').selectOption('5');
    await page.getByLabel('Subject').selectOption('1');
    await page.getByRole('button', { name: 'Generate question paper' }).click();

    await expect.poll(() => generationPayload?.subject_code).toBe('21526');
    expect(generationPayload).toMatchObject({
      subject_id: 1,
      subject: 'Advance Java',
      subject_code: '21526',
      branch: 'Computer Engineering',
      semester: 5,
    });
    await expect(page.getByText('Review Generated Paper', { exact: true })).toBeVisible();
  });

  test('Escape closes the sign-in modal', async ({ page }) => {
    await page.goto(baseURL);
    await page.getByRole('button', { name: facultyCard }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toHaveCount(0);
  });

  test('admin sidebar sections load content and update the active item', async ({ page }) => {
    const sections = [
      ['Upload Question Paper', 'Upload Question Paper'],
      ['RUA Extraction', 'RUA Extraction'],
      ['Faculty Management', 'Faculty Management'],
      ['Assign Duties', 'Assign Duties'],
      ['Finalized Papers', 'Uploaded Question Papers'],
      ['Review Papers', 'Section Under Construction'],
      ['Approval Workflow', 'Approval Workflow'],
    ] as const;

    await page.goto(baseURL);
    await page.evaluate(() => {
      sessionStorage.setItem('adminAuthenticated', 'true');
      sessionStorage.setItem('adminToken', 'playwright-admin-token');
    });
    await page.route('**/api/stats', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          stats: {
            total_papers: 0,
            total_questions: 0,
            papers_by_branch: {},
            papers_by_semester: [],
          },
        }),
      }),
    );
    await page.goto(`${baseURL}/admin-dashboard`);
    for (const [item, expectedText] of sections) {
      const navigationButton = page.getByRole('button', { name: item, exact: true });
      await navigationButton.click();
      await expect(page.getByText(expectedText, { exact: false }).first()).toBeVisible();
      await expect(navigationButton).toHaveClass(/bg-gradient-to-r/);
    }
    for (const removedSection of [
      'AI Monitoring',
      'Reports & Analytics',
      'System Settings',
    ]) {
      await expect(page.getByRole('button', { name: removedSection, exact: true })).toHaveCount(0);
    }
  });

  test('admin dashboard redirects when there is no admin session', async ({ page }) => {
    await page.goto(`${baseURL}/admin-dashboard`);
    await expect(page).toHaveURL(`${baseURL}/`);
  });

  test('admin logout clears the session and blocks direct access', async ({ page }) => {
    await page.goto(baseURL);
    await page.evaluate(() => {
      sessionStorage.setItem('adminAuthenticated', 'true');
      sessionStorage.setItem('adminToken', 'playwright-admin-token');
      sessionStorage.setItem('authToken', 'playwright-admin-token');
    });
    await page.route('**/api/stats', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          stats: {
            total_papers: 0,
            total_questions: 0,
            papers_by_branch: {},
            papers_by_semester: [],
          },
        }),
      }),
    );
    await page.goto(`${baseURL}/admin-dashboard`);
    await page.getByRole('button', { name: 'Logout', exact: true }).click();
    await expect(page).toHaveURL(`${baseURL}/`);
    expect(await page.evaluate(() => [
      sessionStorage.getItem('adminAuthenticated'),
      sessionStorage.getItem('adminToken'),
      sessionStorage.getItem('authToken'),
    ])).toEqual([null, null, null]);

    await page.goto(`${baseURL}/admin-dashboard`);
    await expect(page).toHaveURL(`${baseURL}/`);
  });

  test('landing, modal and admin overview fit common viewport widths', async ({ page }, testInfo) => {
    await page.route('**/api/stats', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          stats: {
            total_papers: 0,
            total_questions: 0,
            papers_by_branch: {},
            papers_by_semester: [],
          },
        }),
      }),
    );
    for (const width of [375, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(baseURL);
      await expect(page.getByRole('heading', { name: 'Choose Your Dashboard' })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await page.screenshot({ path: testInfo.outputPath(`landing-${width}.png`), fullPage: true });

      if (width === 375) {
        await page.getByRole('button', { name: facultyCard }).click();
        await expect(page.getByRole('dialog')).toBeVisible();
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
        await page.screenshot({ path: testInfo.outputPath('signin-375.png'), fullPage: true });
      }

      await page.evaluate(() => {
        sessionStorage.setItem('adminAuthenticated', 'true');
        sessionStorage.setItem('adminToken', 'playwright-admin-token');
      });
      await page.goto(`${baseURL}/admin-dashboard`);
      await expect(page.getByRole('heading', { name: 'System Admin Portal' })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await page.screenshot({ path: testInfo.outputPath(`admin-${width}.png`), fullPage: true });
    }
  });
});
