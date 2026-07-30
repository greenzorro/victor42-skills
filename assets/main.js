/*
 * File: main.js
 * Project: victor42-skills
 * Description: Catalog page — load data.json and render skill cards
 */

const DATA_URL = './data.json?v=20260730';
const SITE_DATE_MODIFIED = '2026-07-30';
const OG_IMAGE_URL = 'https://skills.victor42.work/assets/og-image.png';

document.addEventListener('DOMContentLoaded', function() {
    SkillsShared.initShell();
    loadCatalog();
});

async function loadCatalog() {
    try {
        const response = await fetch(DATA_URL);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        renderCatalog(data);
        updateCatalogMeta(data);
    } catch (error) {
        console.error('Could not load skills:', error);
        document.getElementById('error').style.display = 'block';
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

window.onLanguageChange = function() {
    if (!window.__catalogData) return;
    renderCatalog(window.__catalogData);
    updateCatalogMeta(window.__catalogData);
};

function renderCatalog(data) {
    window.__catalogData = data;

    document.getElementById('description').textContent =
        SkillsShared.getText(data.description);
    document.getElementById('site-title').textContent =
        SkillsShared.getText(data.title);

    const parentLink = document.getElementById('parent-link');
    parentLink.href = data.site.parentSite;
    parentLink.textContent = `← ${SkillsShared.getText(data.site.parentLabel)}`;

    const grid = document.getElementById('skills-grid');
    grid.replaceChildren();
    data.skills.forEach(function(skill) {
        grid.appendChild(createSkillCard(skill));
    });

    SkillsShared.renderFooter(data.site);
    document.getElementById('content').style.display = 'block';
}

function createSkillCard(skill) {
    const card = document.createElement('a');
    card.className = 'skill-card';
    card.href = `./${skill.slug}/`;
    card.setAttribute('aria-label', SkillsShared.getText(skill.name));

    const emoji = document.createElement('div');
    emoji.className = 'skill-emoji';
    emoji.setAttribute('aria-hidden', 'true');
    emoji.textContent = skill.emoji;

    const name = document.createElement('h3');
    name.className = 'skill-name';
    name.textContent = SkillsShared.getText(skill.name);

    const summary = document.createElement('p');
    summary.className = 'skill-summary';
    summary.textContent = SkillsShared.getText(skill.summary);

    card.append(emoji, name, summary);
    return card;
}

function updateCatalogMeta(data) {
    const title = SkillsShared.getText(data.title);
    const description = SkillsShared.getText(data.description);

    document.title = title;
    document.getElementById('page-title').textContent = title;

    setMetaContent('description', description);
    setMetaContent('og:title', title, 'property');
    setMetaContent('og:description', description, 'property');
    setMetaContent('twitter:title', title);
    setMetaContent('twitter:description', description);

    updateStructuredData(data);
}

function setMetaContent(selector, value, attr) {
    attr = attr || 'name';
    const el = document.querySelector(`meta[${attr}="${selector}"]`);
    if (el) el.setAttribute('content', value);
}

function updateStructuredData(data) {
    const script = document.getElementById('structured-data');
    const itemList = data.skills.map(function(skill, index) {
        return {
            '@type': 'ListItem',
            position: index + 1,
            item: {
                '@type': 'SoftwareApplication',
                name: SkillsShared.getText(skill.name),
                description: SkillsShared.getText(skill.summary),
                url: `${data.site.origin}/${skill.slug}/`,
                codeRepository: data.site.github,
                downloadUrl: `${data.site.cdnBase}/${skill.zipFile}`,
                applicationCategory: 'DeveloperApplication'
            }
        };
    });

    script.textContent = JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: SkillsShared.getText(data.title),
        url: `${data.site.origin}/`,
        description: SkillsShared.getText(data.description),
        image: OG_IMAGE_URL,
        author: {
            '@type': 'Person',
            name: 'Victor42',
            url: data.site.parentSite
        },
        publisher: {
            '@type': 'Person',
            name: 'Victor42',
            url: data.site.parentSite,
            logo: {
                '@type': 'ImageObject',
                url: 'https://victor42.work/assets/images/favicon.ico'
            }
        },
        inLanguage: SkillsShared.getLanguage() === 'zh' ? 'zh-CN' : 'en',
        dateModified: SITE_DATE_MODIFIED,
        mainEntity: {
            '@type': 'ItemList',
            numberOfItems: data.skills.length,
            itemListElement: itemList
        }
    });
}
