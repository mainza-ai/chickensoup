import SwiftUI

struct WikiPageDetailView: View {
    let detail: APIWikiPageDetail

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                headerSection
                Divider()
                tagsSection
                if !detail.sources.isEmpty {
                    sourcesSection
                }
                if !detail.related.isEmpty {
                    relatedSection
                }
                Divider()
                bodySection
            }
            .padding()
        }
        .background(DesignConstants.warmBackground)
        .navigationTitle(detail.title)
        .toolbar {
                    ToolbarItem(placement: .primaryAction) {
                        ShareLink(item: detail.title + "\n\n" + detail.body)
                    }
                }
            }

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Text(detail.pageType.capitalized)
                    .font(.caption)
                    .fontWeight(.bold)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(typeColor.opacity(0.15))
                    .foregroundStyle(typeColor)
                    .clipShape(Capsule())

                if detail.protected {
                    Label("Protected", systemImage: "lock.fill")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.systemOrange)
                }
            }

            HStack(spacing: 16) {
                if !detail.created.isEmpty {
                    Label(detail.created, systemImage: "calendar")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
                if !detail.updated.isEmpty {
                    Label("Updated \(detail.updated)", systemImage: "arrow.triangle.2.circlepath")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
            }
        }
    }

    private var tagsSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Tags")
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.primaryText)
            if detail.tags.isEmpty {
                Text("None")
                    .font(.caption)
                    .foregroundStyle(DesignConstants.secondaryText)
            } else {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 100))], spacing: 4) {
                    ForEach(detail.tags, id: \.self) { tag in
                        Text(tag)
                            .font(.caption2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(DesignConstants.systemBlue.opacity(0.1))
                            .foregroundStyle(DesignConstants.systemBlue)
                            .clipShape(Capsule())
                    }
                }
            }
        }
    }

    private var sourcesSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Sources")
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.primaryText)
            ForEach(detail.sources, id: \.self) { source in
                Text("• \(source)")
                    .font(.caption)
                    .foregroundStyle(DesignConstants.secondaryText)
            }
        }
    }

    private var relatedSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Related")
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.primaryText)
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 120))], spacing: 4) {
                ForEach(detail.related, id: \.self) { rel in
                    Text(rel)
                        .font(.caption2)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(DesignConstants.systemPurple.opacity(0.1))
                        .foregroundStyle(DesignConstants.systemPurple)
                        .clipShape(Capsule())
                }
            }
        }
    }

    private var bodySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Content")
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.primaryText)
            Text(detail.body)
                .font(.body)
                .foregroundStyle(DesignConstants.primaryText)
                .lineSpacing(4)
        }
    }

    private var typeColor: Color {
        switch detail.pageType {
        case "entities": return DesignConstants.systemBlue
        case "concepts": return DesignConstants.systemPurple
        case "projects": return DesignConstants.systemGreenText
        default: return DesignConstants.secondaryText
        }
    }
}
