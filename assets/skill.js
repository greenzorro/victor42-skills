/*
 * File: skill.js
 * Project: victor42-skills
 * Description: Skill detail page — copy install prompt, theme, language
 */

document.addEventListener('DOMContentLoaded', function() {
    SkillsShared.initShell();

    document.getElementById('copy-btn').addEventListener('click', handleCopy);

    const siteData = JSON.parse(document.getElementById('site-data').textContent);
    SkillsShared.renderFooter(siteData);
});

async function handleCopy() {
    const lang = SkillsShared.getLanguage();
    const pre = document.querySelector(`#install-${lang} pre`);
    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn.dataset.copying === '1') return;

    try {
        await SkillsShared.copyText(pre.textContent);
        const label = copyBtn.querySelector(`[data-lang="${lang}"]`);
        const original = label.textContent;
        copyBtn.dataset.copying = '1';
        label.textContent = SkillsShared.getUi('copied');
        copyBtn.classList.add('is-copied');

        window.setTimeout(function() {
            label.textContent = original;
            copyBtn.classList.remove('is-copied');
            copyBtn.dataset.copying = '0';
        }, 1600);
    } catch (error) {
        console.error('Copy failed:', error);
    }
}
