---
name: setup-pr-branch
description: Set up a local branch that tracks a fork PR and can be pushed back to it, without fetching the whole fork. Use when the user asks to "checkout/setup a PR locally", "setup tracking for PR #N", or wants to push changes to an open pull request from a fork.
---

# Set Up a Fork PR Branch for Pushing

The goal is a local branch that (a) tracks the fork's PR branch and (b) can be pushed back to update
the PR. Two facts matter:

- GitHub's `refs/pull/N/head` is **read-only**; you cannot push to it.
- Maintainers push to a fork PR by pushing to the **base repository** using the fork's branch name.
  GitHub routes that push to the open PR's head when "allow edits from maintainers" is on.

So a fork remote must be configured with a **fetch URL pointing at the fork** and a **push URL
pointing at the base repo** (`git@github.com:Nuitka/Nuitka.git`).

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

Then, whether new or existing, force the correct URLs:

```bash
git remote set-url     <owner> git@github.com:<owner>/Nuitka.git   # fetch: the fork
git remote set-url --push <owner> git@github.com:Nuitka/Nuitka.git  # push: the base repo
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

Because the local name (`pr-<N>`) now differs from the PR branch name, always push with the explicit
form in the next step.

## 5. Push back (updates the PR)

```bash
git push <owner> HEAD:<branch>
```

Use `git push --force <owner> HEAD:<branch>` only after a rebase. GitHub applies these commits to
the open PR automatically.

## Notes / pitfalls

- `gh pr checkout <N>` fetches the **entire** fork and sets the push URL to the fork, so pushing
  then fails with `permission denied`. Prefer the manual steps above when the goal is to push.
- A pre-push hook (`autoformat`) can hang or be slow;
- If `git status` later reports the branch "diverged" from `<owner>/<branch>`, it is usually a stale
  remote-tracking ref: `git fetch <owner> <branch>` refreshes it.
- Because the local branch is named `pr-<N>` while the remote branch keeps the fork's name, a bare
  `git push` will not know where to go (with `push.default=simple` it would even refuse). Always use
  `git push <owner> HEAD:<branch>`.
