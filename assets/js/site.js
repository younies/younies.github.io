// Small touches on top of the static pages.

// The switch in the header flips between the light and dark themes. The choice
// is remembered; picking the theme that matches the system setting goes back
// to following the system.
{
  const root = document.documentElement;
  const system = matchMedia('(prefers-color-scheme: dark)');
  document.querySelector('.theme-toggle')?.addEventListener('click', () => {
    const dark = root.dataset.theme ? root.dataset.theme === 'dark' : system.matches;
    const next = dark ? 'light' : 'dark';
    const followSystem = next === (system.matches ? 'dark' : 'light');
    if (followSystem) delete root.dataset.theme;
    else root.dataset.theme = next;
    try {
      if (followSystem) localStorage.removeItem('theme');
      else localStorage.setItem('theme', next);
    } catch {
      // Storage can be off (for example, in private windows); the switch still
      // works on this page.
    }
  });
}

// Shows the "Upcoming" badge on talks and meetups that haven't happened yet.
{
  const now = new Date();
  const today = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('-');
  for (const item of document.querySelectorAll('[data-event-date]')) {
    if (item.dataset.eventDate >= today) {
      for (const badge of item.querySelectorAll('.upcoming')) badge.hidden = false;
    }
  }
}

// Adds the language name and a Copy button to each code block.
for (const pre of document.querySelectorAll('.prose pre')) {
  const block = pre.parentElement.matches('div.sourceCode') ? pre.parentElement : pre;
  const wrapper = document.createElement('div');
  wrapper.className = 'code-block';
  block.replaceWith(wrapper);
  wrapper.append(block);

  const tools = document.createElement('div');
  tools.className = 'code-tools';
  const language = [...pre.classList].find((name) => !['sourceCode', 'numberSource'].includes(name));
  if (language) {
    const label = document.createElement('span');
    label.textContent = language;
    tools.append(label);
  }
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Copy';
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(pre.innerText.replace(/\n$/, ''));
      button.textContent = 'Copied';
    } catch {
      button.textContent = 'Select and copy';
    }
    setTimeout(() => { button.textContent = 'Copy'; }, 1500);
  });
  tools.append(button);
  wrapper.append(tools);
}
