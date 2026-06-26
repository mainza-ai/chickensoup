import SwiftUI

struct WikiPageDetailView: View {
    let detail: APIWikiPageDetail?

    @StateObject var loader: WikiPageLoader
    @State private var loadedDetail: APIWikiPageDetail? = nil

    init(detail: APIWikiPageDetail) {
        self.detail = detail
        self._loader = StateObject(wrappedValue: WikiPageLoader(slug: detail.slug, pageType: detail.pageType))
        self.loadedDetail = detail
    }

    init(loader: WikiPageLoader) {
        self.detail = nil
        self._loader = StateObject(wrappedValue: loader)
    }

    var body: some View {
        Group {
            if let d = loadedDetail {
                detailContent(d)
            } else if loader.isLoading {
                ProgressView("Loading page...")
            } else if let d = loader.detail {
                let _ = Task { loadedDetail = d }
                detailContent(d)
            } else {
                VStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.largeTitle)
                        .foregroundStyle(DesignConstants.secondaryText)
                    Text(loader.error ?? "Failed to load page")
                        .font(.subheadline)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
            }
        }
        .background(DesignConstants.warmBackground)
        .task {
            if detail == nil {
                await loader.load()
                if let d = loader.detail {
                    loadedDetail = d
                }
            }
        }
    }

    private func detailContent(_ d: APIWikiPageDetail) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                headerSection(d)
                Divider()
                tagsSection(d)
                if !d.sources.isEmpty {
                    sourcesSection(d)
                }
                if !d.related.isEmpty {
                    relatedSection(d)
                }
                Divider()
                bodySection(d)
            }
            .padding()
        }
        .navigationTitle(d.title)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                ShareLink(item: d.title + "\n\n" + d.body)
            }
        }
    }

    private func headerSection(_ d: APIWikiPageDetail) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Text(d.pageType.capitalized)
                    .font(.caption)
                    .fontWeight(.bold)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(typeColor(d.pageType).opacity(0.15))
                    .foregroundStyle(typeColor(d.pageType))
                    .clipShape(Capsule())

                if d.protected {
                    Label("Protected", systemImage: "lock.fill")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.systemOrange)
                }
            }

            HStack(spacing: 16) {
                if !d.created.isEmpty {
                    Label(d.created, systemImage: "calendar")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
                if !d.updated.isEmpty {
                    Label("Updated \(d.updated)", systemImage: "arrow.triangle.2.circlepath")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
            }
        }
    }

    private func tagsSection(_ d: APIWikiPageDetail) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Tags")
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.primaryText)
            if d.tags.isEmpty {
                Text("None")
                    .font(.caption)
                    .foregroundStyle(DesignConstants.secondaryText)
            } else {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 100))], spacing: 4) {
                    ForEach(d.tags, id: \.self) { tag in
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

    private func sourcesSection(_ d: APIWikiPageDetail) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Sources")
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.primaryText)
            ForEach(d.sources, id: \.self) { source in
                Text("• \(source)")
                    .font(.caption)
                    .foregroundStyle(DesignConstants.secondaryText)
            }
        }
    }

    private func relatedSection(_ d: APIWikiPageDetail) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Related")
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.primaryText)
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 120))], spacing: 4) {
                ForEach(d.related, id: \.self) { rel in
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

    private func bodySection(_ d: APIWikiPageDetail) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Content")
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.primaryText)
            Text(d.body)
                .font(.body)
                .foregroundStyle(DesignConstants.primaryText)
                .lineSpacing(4)
        }
    }

    private func typeColor(_ type: String) -> Color {
        switch type {
        case "entities": return DesignConstants.systemBlue
        case "concepts": return DesignConstants.systemPurple
        case "projects": return DesignConstants.systemGreenText
        default: return DesignConstants.secondaryText
        }
    }
}
