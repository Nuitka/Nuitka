---
name: setup-pr-branch
description: Set up a local branch that tracks a fork PR and can be pushed back to it, without fetching the whole fork. Use when the user asks to "checkout/setup a PR locally", "setup tracking for PR #N", or wants to push changes to an open pull request from a fork.
---

# Set Up a Fork PR Branch for Pushing

The goal is a local branch that (a) tracks the fork's PR branch and (b) can be pushed back to update
the PR. Two facts matter:

- GitHub's `refs/pull/N/head` is **read-only**; you cannot push to it.
- Maintainers push to a fork PR by pushing to the **fork** itself. When "allow edits from
  maintainers" is enabled, GitHub grants the maintainer temporary write access to the fork's PR
  branch, so the push updates the PR head directly.

So a fork remote must have **both its fetch and push URLs pointing at the fork**
(`git@github.com:<owner>/Nuitka.git`).

## 1. Discover the PR head

```bash
gh pr view <N> --json headRepositoryOwner,headRefName,baseRefName \
  --jq '{owner: .headRepositoryOwner.login, branch: .headRefName, base: .baseRefName}'
```

Remember `owner` and `branch`. `owner` is usually the GitHub username, lowercase.

## 2. Create/repair the fork remote

Use the owner's login as the remote name. If it does not exist yet:

```bash
git remote add <owner> git@github.com:<owner>/Nuitka.git
```

`git remote add` sets both fetch and push URLs to the fork. If a previous wrong setup left a
`--push` override, restore it to the fork:

```bash
git remote set-url --push <owner> git@github.com:<owner>/Nuitka.git
```

Do **not** use `git remote update <owner>` or `git fetch <owner>` with no refspec: that fetches
every branch of the fork.

## 3. Fetch only the PR branch

```bash
git fetch <owner> <branch>
```

With the default `+refs/heads/*:refs/remotes/<owner>/*` refspec, this fetches exactly one branch and
creates/updates `refs/remotes/<owner>/<branch>`, nothing else.

## 4. Check out with tracking

Name the local branch `pr-<N>` for clarity (the fork's branch name is often generic). This also
makes it unambiguous which PR you are on.

```bash
git checkout -b pr-<N> --track <owner>/<branch>
```

If the branch already exists, just fix its upstream instead:

```bash
git branch --set-upstream-to=<owner>/<branch> pr-<N>
```

## 5. Push back (updates the PR)

```bash
git push <owner> HEAD:<branch>
```

Use `git push --force <owner> HEAD:<branch>` only after a rebase. GitHub applies these commits to
the open PR automatically.

## Notes / pitfalls

- `gh pr checkout <N>` fetches the **entire** fork; prefer the manual steps above to fetch only the
  single PR branch.
- A pre-push hook (`autoformat`) runs `git diff <remote>..<local>` and can list many files when the
  local and remote branches have diverged; that is only the check, not the push payload. If the hook
  itself hangs or is slow, `--no-verify` skips it, but run the autoformatter yourself first.
- If `git status` reports the branch "diverged" from `<owner>/<branch>`, it is usually a stale
  remote-tracking ref: `git fetch <owner> <branch>` refreshes it.
- Because the local branch is named `pr-<N>` while the remote branch keeps the fork's name, a bare
  `git push` refuses (`push.default=simple` requires the names to match). Use
  `git push <owner> HEAD:<branch>`, or `git config push.default upstream` (repo-local) to make bare
  `git push` follow the upstream.
