// Small touches on top of the static pages.

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
