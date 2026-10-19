-- Points links between pages at the built site, so the same Markdown links
-- work on GitHub and on the site:
--
--   [post](other-post.md)     -> other-post.html
--   [notes](README.md)        -> the README on GitHub (README files are not
--                                part of the site)
--
-- tools/build.py sets SITE_REPO to the repository's address on GitHub.

local repo = os.getenv('SITE_REPO') or ''
local source = PANDOC_STATE.input_files[1] or ''

-- Joins a relative link to the folder of the page and resolves `.` and `..`.
local function resolve(link)
  local folder = source:match('^(.*)/[^/]*$')
  local path = folder and (folder .. '/' .. link) or link
  local parts = {}
  for part in path:gmatch('[^/]+') do
    if part == '..' then
      table.remove(parts)
    elseif part ~= '.' then
      table.insert(parts, part)
    end
  end
  return table.concat(parts, '/')
end

function Link(link)
  local target = link.target
  -- Leave other sites, absolute paths, and anchors alone.
  if target:match('^%a[%w+.-]*:') or target:match('^[/#]') then
    return nil
  end
  local path, rest = target:match('^([^?#]*)(.*)$')
  if path == 'README.md' or path:match('/README%.md$') then
    if repo ~= '' then
      -- In GitHub addresses, HEAD stands for the default branch.
      link.target = repo .. '/blob/HEAD/' .. resolve(path) .. rest
      return link
    end
  elseif path:match('%.md$') then
    link.target = path:gsub('%.md$', '.html') .. rest
    return link
  end
end
