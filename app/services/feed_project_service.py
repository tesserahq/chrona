from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import faker

from app.models.project import Project
from app.models.source import Source
from app.models.author import Author
from app.models.source_author import SourceAuthor
from app.models.entry import Entry
from app.models.comment import Comment
from app.models.digest import Digest
from app.models.digest_generation_config import DigestGenerationConfig
from app.services.source_service import SourceService
from app.services.author_service import AuthorService
from app.services.source_author_service import SourceAuthorService
from app.services.entry_service import EntryService
from app.services.comment_service import CommentService
from app.services.digest_service import DigestService
from app.services.digest_generation_config_service import DigestGenerationConfigService
from app.schemas.source import SourceCreate
from app.schemas.author import AuthorCreate
from app.schemas.entry import EntryCreate
from app.schemas.comment import CommentCreate
from app.schemas.digest import DigestCreate
from app.schemas.digest_generation_config import DigestGenerationConfigCreate


class FeedProjectService:
    """Service for feeding a project with fake GitHub data and generating digests."""

    def __init__(self, db: Session):
        self.db = db
        self.fake = faker.Faker()
        self.source_service = SourceService(db)
        self.author_service = AuthorService(db)
        self.source_author_service = SourceAuthorService(db)
        self.entry_service = EntryService(db)
        self.comment_service = CommentService(db)
        self.digest_service = DigestService(db)
        self.digest_generation_config_service = DigestGenerationConfigService(db)

    def feed_project(
        self, project: Project, num_entries: int = 50, num_digests: int = 20
    ) -> Dict[str, Any]:
        """
        Feed a project with fake GitHub data and generate digests.

        Args:
            project: The project to feed
            num_entries: Number of entries to generate (default: 50)
            num_digests: Number of digests to generate (default: 20)

        Returns:
            Dictionary with statistics about what was created
        """
        # Create GitHub source if it doesn't exist
        github_source = self._get_or_create_github_source(project.workspace_id)

        # Create fake authors
        authors = self._create_fake_authors(project.workspace_id, github_source.id)

        # Create entries with comments
        entries = self._create_fake_entries(
            project, github_source.id, authors, num_entries
        )

        # Create digest generation configs
        digest_configs = self._create_digest_generation_configs(project.id, num_digests)

        # Generate digests
        digests = self._generate_digests(project.id, entries, digest_configs)

        return {
            "source_created": github_source.id,
            "authors_created": len(authors),
            "entries_created": len(entries),
            "comments_created": sum(len(entry.comments) for entry in entries),
            "digest_configs_created": len(digest_configs),
            "digests_created": len(digests),
        }

    def _get_or_create_github_source(self, workspace_id: UUID) -> Source:
        """Get or create a GitHub source."""
        return self.source_service.get_or_create_source_by_identifier(
            identifier="github.com",
            workspace_id=workspace_id,
            name="GitHub",
            description="GitHub repository source",
        )

    def _create_fake_authors(
        self, workspace_id: UUID, source_id: UUID, count: int = 20
    ) -> List[Author]:
        """Create fake GitHub authors."""
        authors = []

        for _ in range(count):
            # Create author
            author_data = AuthorCreate(
                display_name=self.fake.name(),
                avatar_url=f"https://avatars.githubusercontent.com/u/{self.fake.random_int(min=1, max=1000000)}?v=4",
                email=self.fake.email(),
                tags=["github", "contributor"],
                labels={"platform": "github", "verified": self.fake.boolean()},
                meta_data={
                    "followers": self.fake.random_int(min=0, max=10000),
                    "public_repos": self.fake.random_int(min=0, max=500),
                    "location": self.fake.city() if self.fake.boolean() else None,
                    "company": self.fake.company() if self.fake.boolean() else None,
                },
            )

            author = self.author_service.create_author(author_data, workspace_id)
            authors.append(author)

            # Create source author mapping
            source_author_data = {
                "author_id": author.id,
                "source_id": source_id,
                "source_author_id": str(self.fake.random_int(min=1, max=1000000)),
            }
            self.source_author_service.get_or_create_source_author(
                source_id, author.id, source_author_data["source_author_id"]
            )

        return authors

    def _create_fake_entries(
        self, project: Project, source_id: UUID, authors: List[Author], count: int
    ) -> List[Entry]:
        """Create fake GitHub entries (issues, PRs, commits)."""
        entries = []

        # Get source authors for the GitHub source
        source_authors = self.source_author_service.get_source_authors_by_source(
            source_id
        )

        for i in range(count):
            entry_type = random.choice(["issue", "pull_request", "commit"])
            author = random.choice(source_authors)

            if entry_type == "issue":
                title, body, tags = self._generate_issue_data()
            elif entry_type == "pull_request":
                title, body, tags = self._generate_pull_request_data()
            else:  # commit
                title, body, tags = self._generate_commit_data()

            entry_data = EntryCreate(
                title=title,
                body=body,
                source_id=source_id,
                external_id=f"gh-{self.fake.random_int(min=1, max=100000)}-{self.fake.uuid4()}",
                tags=tags,
                labels={
                    "type": entry_type,
                    "state": random.choice(["open", "closed", "merged"]),
                    "priority": random.choice(["low", "medium", "high"]),
                    "area": random.choice(
                        ["frontend", "backend", "infrastructure", "docs", "testing"]
                    ),
                },
                meta_data={
                    "created_at": self.fake.date_time_between(
                        start_date="-1y", end_date="now"
                    ).isoformat(),
                    "updated_at": self.fake.date_time_between(
                        start_date="-6m", end_date="now"
                    ).isoformat(),
                    "repository": f"{self.fake.user_name()}/{self.fake.word()}",
                    "url": f"https://github.com/{self.fake.user_name()}/{self.fake.word()}/{entry_type}s/{self.fake.random_int(min=1, max=1000)}",
                    "reactions": {
                        "👍": self.fake.random_int(min=0, max=50),
                        "👎": self.fake.random_int(min=0, max=10),
                        "❤️": self.fake.random_int(min=0, max=30),
                        "🎉": self.fake.random_int(min=0, max=20),
                    },
                },
                source_author_id=author.id,
                project_id=project.id,
            )

            entry = self.entry_service.create_entry(entry_data)

            # Create comments for this entry
            num_comments = random.randint(0, 8)
            for _ in range(num_comments):
                comment_author = random.choice(source_authors)
                comment_data = CommentCreate(
                    body=self._generate_comment_body(),
                    source_author_id=comment_author.id,
                    entry_id=entry.id,
                    tags=["github", "comment"],
                    labels={"type": "comment"},
                    meta_data={
                        "created_at": self.fake.date_time_between(
                            start_date=datetime.fromisoformat(
                                entry.meta_data["created_at"].replace("Z", "+00:00")
                            ),
                            end_date="now",
                        ).isoformat(),
                        "reactions": {
                            "👍": self.fake.random_int(min=0, max=10),
                            "👎": self.fake.random_int(min=0, max=3),
                            "❤️": self.fake.random_int(min=0, max=5),
                        },
                    },
                    external_id=f"comment-{self.fake.random_int(min=1, max=100000)}-{self.fake.uuid4()}",
                    source_id=source_id,
                )
                self.comment_service.create_comment(comment_data)

            # Reload entry with comments
            entry = self.entry_service.get_entry(entry.id)
            entries.append(entry)

        return entries

    def _generate_issue_data(self) -> tuple[str, str, List[str]]:
        """Generate fake issue data."""
        issue_templates = [
            (
                "Bug: {title}",
                "## Description\n{description}\n\n## Steps to Reproduce\n1. {step1}\n2. {step2}\n3. {step3}\n\n## Expected Behavior\n{expected}\n\n## Actual Behavior\n{actual}",
            ),
            (
                "Feature Request: {title}",
                "## Summary\n{description}\n\n## Motivation\n{motivation}\n\n## Proposed Solution\n{solution}\n\n## Additional Context\n{context}",
            ),
            (
                "Enhancement: {title}",
                "## Current Behavior\n{current}\n\n## Desired Behavior\n{desired}\n\n## Implementation Ideas\n{ideas}",
            ),
        ]

        template = random.choice(issue_templates)
        title_template, body_template = template

        title = title_template.format(title=self.fake.sentence(nb_words=6).rstrip("."))
        body = body_template.format(
            description=self.fake.paragraph(),
            step1=self.fake.sentence(),
            step2=self.fake.sentence(),
            step3=self.fake.sentence(),
            expected=self.fake.sentence(),
            actual=self.fake.sentence(),
            motivation=self.fake.paragraph(),
            solution=self.fake.paragraph(),
            context=self.fake.paragraph(),
            current=self.fake.paragraph(),
            desired=self.fake.paragraph(),
            ideas=self.fake.paragraph(),
        )

        tags = [
            "issue",
            "bug" if "Bug" in title else "enhancement",
            random.choice(["frontend", "backend", "infrastructure"]),
        ]

        return title, body, tags

    def _generate_pull_request_data(self) -> tuple[str, str, List[str]]:
        """Generate fake pull request data."""
        pr_templates = [
            (
                "Add {feature}",
                "## Description\n{description}\n\n## Changes Made\n- {change1}\n- {change2}\n- {change3}\n\n## Testing\n{testing}\n\n## Screenshots\n{screenshots}",
            ),
            (
                "Fix {issue}",
                "## Description\n{description}\n\n## Problem\n{problem}\n\n## Solution\n{solution}\n\n## Testing\n{testing}",
            ),
            (
                "Update {component}",
                "## Description\n{description}\n\n## Changes\n{changes}\n\n## Breaking Changes\n{breaking}\n\n## Migration Guide\n{migration}",
            ),
        ]

        template = random.choice(pr_templates)
        title_template, body_template = template

        title = title_template.format(
            feature=self.fake.word(), issue=self.fake.word(), component=self.fake.word()
        )
        body = body_template.format(
            description=self.fake.paragraph(),
            change1=self.fake.sentence(),
            change2=self.fake.sentence(),
            change3=self.fake.sentence(),
            testing=self.fake.paragraph(),
            screenshots=(
                "See attached screenshots" if self.fake.boolean() else "No screenshots"
            ),
            problem=self.fake.paragraph(),
            solution=self.fake.paragraph(),
            changes=self.fake.paragraph(),
            breaking=self.fake.paragraph() if self.fake.boolean() else "None",
            migration=(
                self.fake.paragraph() if self.fake.boolean() else "Not applicable"
            ),
        )

        tags = [
            "pull-request",
            "feature" if "Add" in title else "fix",
            random.choice(["frontend", "backend", "infrastructure"]),
        ]

        return title, body, tags

    def _generate_commit_data(self) -> tuple[str, str, List[str]]:
        """Generate fake commit data."""
        commit_messages = [
            "feat: add {feature}",
            "fix: resolve {issue}",
            "docs: update {documentation}",
            "style: format {component}",
            "refactor: improve {component}",
            "test: add tests for {feature}",
            "chore: update {dependency}",
        ]

        message_template = random.choice(commit_messages)
        title = message_template.format(
            feature=self.fake.word(),
            issue=self.fake.word(),
            documentation=self.fake.word(),
            component=self.fake.word(),
            dependency=self.fake.word(),
        )

        body = f"## Changes\n- {self.fake.sentence()}\n- {self.fake.sentence()}\n\n## Files Modified\n- {self.fake.file_path()}\n- {self.fake.file_path()}\n- {self.fake.file_path()}"

        tags = [
            "commit",
            "git",
            random.choice(
                ["feat", "fix", "docs", "style", "refactor", "test", "chore"]
            ),
        ]

        return title, body, tags

    def _generate_comment_body(self) -> str:
        """Generate fake comment body."""
        comment_templates = [
            "Thanks for the contribution! {comment}",
            "I think we should {suggestion}",
            "This looks good to me. {approval}",
            "Could you please {request}?",
            "I have a question about {question}",
            "This is a great idea! {enthusiasm}",
            "I'm not sure about this approach. {concern}",
            "LGTM! {approval}",
        ]

        template = random.choice(comment_templates)
        return template.format(
            comment=self.fake.sentence(),
            suggestion=self.fake.sentence(),
            approval=self.fake.sentence(),
            request=self.fake.sentence(),
            question=self.fake.sentence(),
            enthusiasm=self.fake.sentence(),
            concern=self.fake.sentence(),
        )

    def _create_digest_generation_configs(
        self, project_id: UUID, count: int
    ) -> List[DigestGenerationConfig]:
        """Create digest generation configurations."""
        configs = []

        digest_types = [
            ("Weekly Summary", "A weekly summary of all project activity"),
            ("Bug Report Digest", "Summary of all bug reports and fixes"),
            ("Feature Update Digest", "Summary of new features and enhancements"),
            ("Code Review Digest", "Summary of code reviews and pull requests"),
            ("Issue Digest", "Summary of open and closed issues"),
            ("Contributor Digest", "Summary of contributor activity"),
            ("Security Digest", "Summary of security-related updates"),
            ("Performance Digest", "Summary of performance improvements"),
        ]

        for i in range(count):
            config_type = random.choice(digest_types)
            config_data = DigestGenerationConfigCreate(
                title=f"{config_type[0]} #{i+1}",
                system_prompt=f"Generate a {config_type[0].lower()} based on the following entries. Focus on the most important and relevant information. Format the output as a clear, concise summary.",
                timezone="UTC",
                cron_expression="0 9 * * 1",  # Every Monday at 9 AM UTC
                tags=[config_type[0].lower().replace(" ", "-"), "auto-generated"],
                labels={
                    "type": config_type[0].lower().replace(" ", "_"),
                    "priority": random.choice(["low", "medium", "high"]),
                    "category": random.choice(["summary", "technical", "community"]),
                    "max_entries": random.randint(5, 20),
                },
            )

            config = (
                self.digest_generation_config_service.create_digest_generation_config(
                    config_data, project_id
                )
            )
            configs.append(config)

        return configs

    def _generate_digests(
        self,
        project_id: UUID,
        entries: List[Entry],
        configs: List[DigestGenerationConfig],
    ) -> List[Digest]:
        """Generate digests based on entries and configurations."""
        digests = []

        for config in configs:
            # Select random entries for this digest
            max_entries = config.labels.get("max_entries", 10)
            selected_entries = random.sample(entries, min(max_entries, len(entries)))
            entry_ids = [entry.id for entry in selected_entries]

            # Get comments for selected entries
            comment_ids = []
            for entry in selected_entries:
                comment_ids.extend([comment.id for comment in entry.comments])

            # Generate digest content
            digest_title = f"{config.title} - {self.fake.date_between(start_date='-1m', end_date='now').strftime('%B %Y')}"
            digest_body = self._generate_digest_content(selected_entries, config)

            digest_data = DigestCreate(
                title=digest_title,
                body=digest_body,
                entries_ids=entry_ids,
                comments_ids=comment_ids,
                tags=config.tags + ["generated", "auto"],
                labels={
                    "type": config.labels.get("type", "summary"),
                    "priority": config.labels.get("priority", "medium"),
                    "category": config.labels.get("category", "summary"),
                    "generated_at": datetime.now().isoformat(),
                },
                from_date=datetime.now() - timedelta(days=7),
                to_date=datetime.now(),
                digest_generation_config_id=config.id,
                project_id=project_id,
            )

            digest = self.digest_service.create_digest(digest_data)
            digests.append(digest)

        return digests

    def _generate_digest_content(
        self, entries: List[Entry], config: DigestGenerationConfig
    ) -> str:
        """Generate digest content based on entries and configuration."""
        content = f"# {config.title}\n\n"
        content += f"*Auto-generated digest based on project entries*\n\n"

        # Group entries by type
        issues = [e for e in entries if e.labels.get("type") == "issue"]
        prs = [e for e in entries if e.labels.get("type") == "pull_request"]
        commits = [e for e in entries if e.labels.get("type") == "commit"]

        if issues:
            content += "## Issues\n\n"
            for issue in issues[:5]:  # Limit to 5 issues
                content += (
                    f"- **{issue.title}** - {issue.labels.get('state', 'unknown')}\n"
                )
                if issue.body:
                    content += f"  - {issue.body[:100]}...\n"
                content += "\n"

        if prs:
            content += "## Pull Requests\n\n"
            for pr in prs[:5]:  # Limit to 5 PRs
                content += f"- **{pr.title}** - {pr.labels.get('state', 'unknown')}\n"
                if pr.body:
                    content += f"  - {pr.body[:100]}...\n"
                content += "\n"

        if commits:
            content += "## Recent Commits\n\n"
            for commit in commits[:10]:  # Limit to 10 commits
                content += f"- {commit.title}\n"
                content += "\n"

        content += f"\n---\n*This digest was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return content
