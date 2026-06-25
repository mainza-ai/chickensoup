import SwiftUI
import SwiftData
import UniformTypeIdentifiers

struct DataIngestionView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \LoreEntity.name) private var localEntities: [LoreEntity]
    @Query(sort: \TemporalEvent.timestamp) private var localEvents: [TemporalEvent]

    @ObservedObject var syncService = SyncService.shared
    @ObservedObject var backendService = BackendService.shared

    @State private var isDraggingOver = false
    @State private var uploadedFiles: [String] = []
    @State private var isExtracting = false
    @State private var isBulkIngesting = false
    @State private var isImporting = false
    @State private var isCommitting = false
    @State private var isProcessingFolder = false
    @State private var selectedFileURL: URL?
    @State private var selectedFileName: String = ""

    @State private var selectedEntityForEdit: LoreEntity? = nil

    @State private var analysisResult: APIAnalyzeResponse? = nil
    @State private var commitResult: APIFileIngestResponse? = nil
    @State private var folderResult: APIFolderIngestResponse? = nil
    @State private var ingestError: String? = nil

    @Namespace private var animationNamespace

    private var averageConfidence: Double {
        localEntities.isEmpty ? 0.0 : localEntities.map { $0.confidence }.reduce(0.0, +) / Double(localEntities.count)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: DesignConstants.loosePadding) {
                statsDashboard
                    .padding(.horizontal)

                dropTargetView
                    .padding(.horizontal)

                if let error = ingestError {
                    errorBanner(error)
                        .padding(.horizontal)
                }

                if isExtracting {
                    loadingSkeletonView
                        .padding(.horizontal)
                } else if let analysis = analysisResult {
                    analysisPreviewView(analysis)
                        .padding(.horizontal)
                }

                if let result = commitResult {
                    commitResultView(result)
                        .padding(.horizontal)
                }

                if isProcessingFolder {
                    HStack {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("Processing folder...")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.systemOrangeText)
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(DesignConstants.cardBackground)
                    .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                } else if let result = folderResult {
                    folderResultView(result)
                        .padding(.horizontal)
                }

                chatContributionsSection
                    .padding(.horizontal)

                localIngestOverview
                    .padding(.horizontal)
            }
            .padding(.vertical, DesignConstants.standardPadding)
        }
        .background(DesignConstants.warmBackground.ignoresSafeArea())
        .navigationTitle("Data Ingest")
        #if !os(macOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        #if os(macOS)
        .fileImporter(
            isPresented: $isImporting,
            allowedContentTypes: [.folder],
            allowsMultipleSelection: false
        ) { result in
            switch result {
            case .success(let urls):
                if let url = urls.first {
                    enumerateAndProcessFolder(url: url)
                }
            case .failure:
                ingestError = "Failed to open folder."
            }
        }
        #else
        .fileImporter(
            isPresented: $isImporting,
            allowedContentTypes: [.data, .zip],
            allowsMultipleSelection: true
        ) { result in
            switch result {
            case .success(let urls):
                handleSelectedURLs(urls)
            case .failure:
                ingestError = "Failed to open file."
            }
        }
        #endif
        .sheet(item: $selectedEntityForEdit) { entity in
            EditAnnotationSheet(entity: entity) { updatedEntity in
                syncService.queueSync(entityId: updatedEntity.id, type: "LoreEntity", action: "update")
                selectedEntityForEdit = nil
            }
        }
    }

    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    private var isCompact: Bool { horizontalSizeClass == .compact }

    // MARK: - Stats Dashboard

    private var statsDashboard: some View {
        VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
            Text("INGEST METRICS & QUALITY")
                .font(.footnote)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.secondaryText)
                .accessibilityAddTraits(.isHeader)

            Group {
                if isCompact {
                    VStack(spacing: DesignConstants.compactPadding) {
                        statCard(
                            label: "Avg Confidence",
                            color: averageConfidence > 0.9 ? DesignConstants.systemGreenText : DesignConstants.systemOrangeText,
                            accessibilityLabel: "Average extraction confidence is \(Int(averageConfidence * 100)) percent"
                        ) {
                            Text(averageConfidence, format: .percent.precision(.fractionLength(1)))
                        }
                        statCard(
                            label: "Total Entities",
                            color: DesignConstants.primaryText,
                            accessibilityLabel: "Total ingested entities is \(localEntities.count)"
                        ) {
                            Text(localEntities.count, format: .number)
                        }
                        syncStatusCard
                    }
                } else {
                    HStack(spacing: DesignConstants.standardPadding) {
                        statCard(
                            label: "Avg Confidence",
                            color: averageConfidence > 0.9 ? DesignConstants.systemGreenText : DesignConstants.systemOrangeText,
                            accessibilityLabel: "Average extraction confidence is \(Int(averageConfidence * 100)) percent"
                        ) {
                            Text(averageConfidence, format: .percent.precision(.fractionLength(1)))
                        }
                        statCard(
                            label: "Total Entities",
                            color: DesignConstants.primaryText,
                            accessibilityLabel: "Total ingested entities is \(localEntities.count)"
                        ) {
                            Text(localEntities.count, format: .number)
                        }
                        syncStatusCard
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func statCard(label: String, color: Color, accessibilityLabel: String, @ViewBuilder value: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption)
                .foregroundStyle(DesignConstants.secondaryText)
            value()
                .font(.title2)
                .fontWeight(.bold)
                .foregroundStyle(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(DesignConstants.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
        .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(accessibilityLabel)
    }

    private var syncStatusCard: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Sync Queue")
                .font(.caption)
                .foregroundStyle(DesignConstants.secondaryText)
            HStack {
                Image(systemName: syncService.isSyncing ? "arrow.triangle.2.circlepath" : "cloud.checkmark.fill")
                    .foregroundStyle(syncService.isSyncing ? DesignConstants.systemOrange : DesignConstants.systemGreen)
                    .symbolEffect(.pulse, isActive: syncService.isSyncing)
                Text("\(syncService.pendingSyncCount) pending")
                    .font(.body)
                    .fontWeight(.medium)
                    .foregroundStyle(DesignConstants.primaryText)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(DesignConstants.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
        .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(syncService.pendingSyncCount) entities pending database synchronization")
    }

    // MARK: - Drop Target View

    private var dropTargetView: some View {
        VStack {
            Image(systemName: "doc.badge.plus")
                .font(.system(size: 40))
                .foregroundStyle(isDraggingOver ? DesignConstants.systemOrange : DesignConstants.systemBlue)
                .padding(.bottom, 8)
                .scaleEffect(isDraggingOver ? 1.15 : 1.0)
                .animation(DesignConstants.hoverAnimation, value: isDraggingOver)

            Text("Import Files or Folders")
                .font(.headline)
                .foregroundStyle(DesignConstants.primaryText)

            Text("TXT, JSON, CSV, MD — single files, zip archives, or entire folders")
                .font(.caption)
                .foregroundStyle(DesignConstants.secondaryText)

            HStack(spacing: 12) {
                Button("Import Files or Folders", systemImage: "doc.badge.plus") {
                    ingestError = nil
                    analysisResult = nil
                    commitResult = nil
                    folderResult = nil
                    isImporting = true
                }
                .buttonStyle(.borderedProminent)
                .tint(DesignConstants.systemBlue)
                .disabled(isExtracting || isCommitting || isBulkIngesting || isProcessingFolder)
                .accessibilityLabel("Import files or folders to ingest into the wiki")

                if isBulkIngesting {
                    HStack(spacing: 8) {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("Ingesting...")
                            .font(.subheadline)
                            .bold()
                            .foregroundStyle(DesignConstants.systemOrangeText)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                } else {
                    Button("Run Bulk Ingest", systemImage: "arrow.triangle.2.circlepath") {
                        runBulkIngestion()
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(DesignConstants.systemOrange)
                    .accessibilityLabel("Run bulk ingestion script to rebuild database from markdown wiki")
                }
            }
            .padding(.top, 12)

            if !uploadedFiles.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Uploaded Intel Sources:")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundStyle(DesignConstants.secondaryText)

                    ForEach(uploadedFiles, id: \.self) { file in
                        HStack {
                            Image(systemName: "doc.text.fill")
                                .foregroundStyle(DesignConstants.secondaryText)
                            Text(file)
                                .font(.caption2)
                                .foregroundStyle(DesignConstants.primaryText)
                        }
                    }
                }
                .padding()
                .background(Color.black.opacity(0.04))
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .padding(.top, 12)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 32)
        .background(
            RoundedRectangle(cornerRadius: DesignConstants.panelCornerRadius)
                .stroke(isDraggingOver ? DesignConstants.systemOrange : DesignConstants.systemBlue.opacity(0.4), style: StrokeStyle(lineWidth: 2, lineCap: .round, lineJoin: .round, dash: [6, 4]))
                .background(DesignConstants.cardBackground)
        )
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.panelCornerRadius))
        .onDrop(of: [UTType.item.identifier], isTargeted: $isDraggingOver) { providers in
            if let item = providers.first {
                item.loadItem(forTypeIdentifier: UTType.data.identifier) { data, error in
                    if let url = data as? URL {
                        DispatchQueue.main.async {
                            handleSelectedURLs([url])
                        }
                    }
                }
            }
            return true
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("File drop area. Drag and drop intel files here.")
    }

    // MARK: - Error Banner

    private func errorBanner(_ message: String) -> some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(DesignConstants.systemRed)
            Text(message)
                .font(.subheadline)
                .foregroundStyle(DesignConstants.primaryText)
            Spacer()
            Button(action: { ingestError = nil }) {
                Image(systemName: "xmark.circle.fill")
                    .foregroundStyle(DesignConstants.secondaryText)
            }
        }
        .padding()
        .background(DesignConstants.systemRed.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
    }

    // MARK: - Loading Skeleton

    private var loadingSkeletonView: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("AI Extraction Preview")
                .font(.headline)
                .foregroundStyle(DesignConstants.primaryText)

            ForEach(0..<3, id: \.self) { _ in
                HStack {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Analyzing content...")
                            .font(.body)
                        Text("Category: detecting...")
                            .font(.caption)
                    }
                    Spacer()
                }
                .padding()
                .background(DesignConstants.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                .skeleton(isLoading: true)
            }
        }
    }

    // MARK: - Analysis Preview

    private func analysisPreviewView(_ analysis: APIAnalyzeResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("AI EXTRACTED \(analysis.suggestedPages.count == 1 ? "PAGE" : "PAGES")")
                    .font(.footnote)
                    .fontWeight(.bold)
                    .foregroundStyle(DesignConstants.secondaryText)

                Spacer()

                if !isCommitting {
                    Button("Commit to Wiki", systemImage: "arrow.up.doc.fill") {
                        commitFile()
                    }
                    .font(.caption)
                    .buttonStyle(.borderedProminent)
                    .tint(DesignConstants.systemGreen)
                    .disabled(isCommitting)
                    .accessibilityLabel("Commit extracted pages to the wiki")

                    Button("Discard", systemImage: "trash") {
                        withAnimation {
                            analysisResult = nil
                            uploadedFiles.removeAll()
                        }
                    }
                    .font(.caption)
                    .buttonStyle(.bordered)
                    .tint(DesignConstants.systemRed)
                } else {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("Writing wiki pages...")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.systemOrangeText)
                }
            }

            if let fileName = selectedFileName.isEmpty ? nil : selectedFileName {
                HStack {
                    Image(systemName: "doc.text")
                        .foregroundStyle(DesignConstants.systemBlue)
                    Text(fileName)
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
                .padding(.bottom, 4)
            }

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: DesignConstants.standardPadding) {
                    ForEach(analysis.suggestedPages) { page in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(page.title)
                                    .font(.headline)
                                    .foregroundStyle(DesignConstants.primaryText)
                                    .lineLimit(2)
                                Spacer()
                                Text(pageTypeLabel(page.pageType))
                                    .font(.caption2)
                                    .fontWeight(.bold)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(typeColor(page.pageType).opacity(0.15))
                                    .foregroundStyle(typeColor(page.pageType))
                                    .clipShape(Capsule())
                            }

                            Text(page.summary)
                                .font(.caption)
                                .foregroundStyle(DesignConstants.secondaryText)
                                .lineLimit(3)

                            HStack {
                                Image(systemName: "percent")
                                    .font(.caption)
                                Text(page.confidence, format: .percent.precision(.fractionLength(0)))
                                    .font(.caption)
                            }
                            .foregroundStyle(page.confidence > 0.9 ? DesignConstants.systemGreenText : DesignConstants.systemOrangeText)

                            if !page.tags.isEmpty {
                                ScrollView(.horizontal, showsIndicators: false) {
                                    HStack(spacing: 4) {
                                        ForEach(page.tags, id: \.self) { tag in
                                            Text("#\(tag)")
                                                .font(.caption2)
                                                .foregroundStyle(DesignConstants.systemBlue)
                                        }
                                    }
                                }
                            }

                            if !page.related.isEmpty {
                                Text("Related: \(page.related.joined(separator: ", "))")
                                    .font(.caption2)
                                    .foregroundStyle(DesignConstants.secondaryText)
                                    .lineLimit(1)
                            }
                        }
                        .frame(width: 240)
                        .padding()
                        .background(DesignConstants.cardBackground)
                        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                        .shadow(color: DesignConstants.glassShadowColor, radius: 6, y: 3)
                    }
                }
                .padding(.vertical, 6)
            }

            if !analysis.suggestedPages.isEmpty {
                Button("Commit All (\(analysis.suggestedPages.count) pages)", systemImage: "arrow.up.doc.fill") {
                    commitFile()
                }
                .buttonStyle(.borderedProminent)
                .tint(DesignConstants.systemGreen)
                .disabled(isCommitting)
            }
        }
    }

    private func pageTypeLabel(_ type: String) -> String {
        switch type {
        case "entities": return "Entity"
        case "concepts": return "Concept"
        case "projects": return "Project"
        default: return type.capitalized
        }
    }

    private func typeColor(_ type: String) -> Color {
        switch type {
        case "entities": return DesignConstants.systemBlue
        case "concepts": return DesignConstants.systemPurple
        case "projects": return DesignConstants.systemGreen
        default: return DesignConstants.systemOrange
        }
    }

    // MARK: - Commit Result View

    private func commitResultView(_ result: APIFileIngestResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: result.success ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                    .foregroundStyle(result.success ? DesignConstants.systemGreen : DesignConstants.systemRed)
                    .font(.title2)
                Text(result.success ? "Ingest Complete" : "Ingest Failed")
                    .font(.headline)
                    .foregroundStyle(DesignConstants.primaryText)
                Spacer()
                Button("Dismiss", systemImage: "xmark") {
                    withAnimation {
                        commitResult = nil
                        analysisResult = nil
                        uploadedFiles.removeAll()
                        selectedFileName = ""
                    }
                }
                .font(.caption)
                .buttonStyle(.bordered)
            }

            if result.success {
                VStack(alignment: .leading, spacing: 6) {
                    if !result.pagesCreated.isEmpty {
                        Label("Pages created: \(result.pagesCreated.joined(separator: ", "))", systemImage: "plus.circle")
                            .font(.caption)
                    }
                    if !result.pagesUpdated.isEmpty {
                        Label("Pages updated: \(result.pagesUpdated.joined(separator: ", "))", systemImage: "arrow.triangle.2.circlepath")
                            .font(.caption)
                    }
                    Label("Neo4j nodes: \(result.nodesCreated), relationships: \(result.relationshipsCreated)", systemImage: "point.3.connected.trianglepath.dotted")
                        .font(.caption)
                }
                .foregroundStyle(DesignConstants.secondaryText)
            }
        }
        .padding()
        .background(DesignConstants.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
        .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
        .transition(.opacity.combined(with: .move(edge: .top)))
    }

    // MARK: - Folder Result View

    private func folderResultView(_ result: APIFolderIngestResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: result.success ? "folder.fill.badge.checkmark" : "exclamationmark.triangle.fill")
                    .foregroundStyle(result.success ? DesignConstants.systemGreen : DesignConstants.systemRed)
                    .font(.title2)
                Text(result.success ? "Folder Ingest Complete" : "Folder Ingest Failed")
                    .font(.headline)
                    .foregroundStyle(DesignConstants.primaryText)
                Spacer()
                Button("Dismiss", systemImage: "xmark") {
                    withAnimation {
                        folderResult = nil
                        uploadedFiles.removeAll()
                    }
                }
                .font(.caption)
                .buttonStyle(.bordered)
            }

            if result.success {
                VStack(alignment: .leading, spacing: 6) {
                    Label("\(result.totalFiles) files processed", systemImage: "doc.on.doc")
                        .font(.caption)
                    if result.totalPagesCreated > 0 {
                        Label("\(result.totalPagesCreated) wiki pages created", systemImage: "plus.circle")
                            .font(.caption)
                    }
                    if result.totalPagesUpdated > 0 {
                        Label("\(result.totalPagesUpdated) wiki pages updated", systemImage: "arrow.triangle.2.circlepath")
                            .font(.caption)
                    }
                    Label("Neo4j: \(result.totalNodesCreated) nodes, \(result.totalRelationshipsCreated) relationships", systemImage: "point.3.connected.trianglepath.dotted")
                        .font(.caption)
                    if !result.fileResults.isEmpty {
                        DisclosureGroup("Per-file breakdown") {
                            ForEach(Array(result.fileResults.enumerated()), id: \.offset) { idx, fileResult in
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("File \(idx + 1)")
                                        .font(.caption)
                                        .fontWeight(.semibold)
                                    if !fileResult.pagesCreated.isEmpty {
                                        Text("Created: \(fileResult.pagesCreated.joined(separator: ", "))")
                                            .font(.caption2)
                                    }
                                    if !fileResult.pagesUpdated.isEmpty {
                                        Text("Updated: \(fileResult.pagesUpdated.joined(separator: ", "))")
                                            .font(.caption2)
                                    }
                                }
                                .padding(.vertical, 4)
                            }
                        }
                        .font(.caption)
                    }
                }
                .foregroundStyle(DesignConstants.secondaryText)
            }
        }
        .padding()
        .background(DesignConstants.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
        .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
        .transition(.opacity.combined(with: .move(edge: .top)))
    }

    // MARK: - Ingested Overview List

    private var localIngestOverview: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("LORE REPOSITORY")
                .font(.footnote)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.secondaryText)

            if localEntities.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "archivebox")
                        .font(.largeTitle)
                        .foregroundStyle(DesignConstants.secondaryText)
                    Text("No local lore entities cataloged yet.")
                        .font(.subheadline)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
                .frame(maxWidth: .infinity)
                .padding()
            } else {
                LazyVStack(spacing: DesignConstants.compactPadding) {
                    ForEach(localEntities) { entity in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(entity.name)
                                    .font(.body)
                                    .fontWeight(.bold)
                                    .foregroundStyle(DesignConstants.primaryText)

                                Text(entity.summary)
                                    .font(.caption)
                                    .foregroundStyle(DesignConstants.secondaryText)
                                    .lineLimit(2)
                            }

                            Spacer()

                            VStack(alignment: .trailing, spacing: 4) {
                                Text(entity.type)
                                    .font(.caption2)
                                    .fontWeight(.bold)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(DesignConstants.systemBlue.opacity(0.15))
                                    .foregroundStyle(DesignConstants.systemBlue)
                                    .clipShape(Capsule())

                                Text("Notes: \(entity.userNotes.isEmpty ? "None" : entity.userNotes)")
                                    .font(.caption2)
                                    .foregroundStyle(DesignConstants.secondaryText)
                                    .lineLimit(1)
                            }
                        }
                        .padding()
                        .background(DesignConstants.cardBackground)
                        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                        .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
                        .onTapGesture {
                            selectedEntityForEdit = entity
                        }
                    }
                }
            }
        }
    }

    // MARK: - Chat Contributions

    private var chatContributionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("CHAT CONTRIBUTIONS")
                .font(.footnote)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.secondaryText)

            if let status = backendService.chatIngestStatus {
                VStack(spacing: 12) {
                    HStack {
                        Image(systemName: status.enabled ? "leaf.fill" : "leaf")
                            .foregroundStyle(status.enabled ? DesignConstants.systemGreenText : DesignConstants.secondaryText)
                        Text(status.enabled ? "Auto-conversion is ON" : "Auto-conversion is OFF")
                            .font(.subheadline)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        Spacer()
                    }

                    if status.enabled {
                        HStack(spacing: 16) {
                            statCard(label: "Pages", color: DesignConstants.systemGreen, accessibilityLabel: "Pages created from chat") {
                                Text("\(status.pagesCreated)")
                                    .font(.title3)
                                    .bold()
                                    .foregroundStyle(DesignConstants.systemGreenText)
                            }
                            statCard(label: "Conversations", color: DesignConstants.systemOrange, accessibilityLabel: "Conversations ingested") {
                                Text("\(status.conversationsIngested)")
                                    .font(.title3)
                                    .bold()
                                    .foregroundStyle(DesignConstants.systemOrangeText)
                            }
                            if let lastRun = status.lastRun {
                                statCard(label: "Last Run", color: DesignConstants.secondaryText, accessibilityLabel: "Last ingest run") {
                                    Text(lastRun.prefix(10))
                                        .font(.caption)
                                        .bold()
                                        .foregroundStyle(DesignConstants.secondaryText)
                                }
                            }
                        }

                        Button("Run Now") {
                            Task {
                                await backendService.triggerChatIngest()
                                await backendService.fetchChatIngestStatus()
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(DesignConstants.systemOrange)
                        .font(.caption)
                        .frame(maxWidth: .infinity)
                    }
                }
                .padding()
                .background(DesignConstants.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
            } else {
                HStack {
                    Spacer()
                    Button("Check Chat Status") {
                        Task {
                            await backendService.fetchChatIngestStatus()
                        }
                    }
                    .font(.subheadline)
                    .buttonStyle(.bordered)
                    Spacer()
                }
            }
        }
    }

    // MARK: - Actions

    private func analyzeFile(url: URL) {
        guard url.startAccessingSecurityScopedResource() else {
            ingestError = "Permission denied for file."
            return
        }
        defer { url.stopAccessingSecurityScopedResource() }

        do {
            let data = try Data(contentsOf: url)
            guard let text = String(data: data, encoding: .utf8) else {
                ingestError = "Could not read file as text."
                return
            }

            isExtracting = true
            ingestError = nil
            analysisResult = nil
            commitResult = nil
            let fileName = url.lastPathComponent

            Task {
                defer {
                    DispatchQueue.main.async { isExtracting = false }
                }
                do {
                    let bodyDict: [String: Any] = ["content": text, "filename": fileName]
                    let bodyData = try JSONSerialization.data(withJSONObject: bodyDict)
                    let response: APIAnalyzeResponse = try await APIClient.shared.request(
                        path: "/ingest/analyze",
                        method: "POST",
                        body: bodyData
                    )
                    await MainActor.run {
                        withAnimation {
                            analysisResult = response
                            uploadedFiles = [fileName]
                        }
                    }
                } catch {
                    await MainActor.run {
                        ingestError = "Analysis failed: \(error.localizedDescription)"
                    }
                }
            }
        } catch {
            ingestError = "Failed to read file: \(error.localizedDescription)"
        }
    }

    private func handleSelectedURLs(_ urls: [URL]) {
        if urls.count == 1, let url = urls.first {
            if url.pathExtension.lowercased() == "zip" {
                selectedFileName = url.lastPathComponent
                uploadFolderToBackend(url: url)
            } else {
                selectedFileURL = url
                selectedFileName = url.lastPathComponent
                analyzeFile(url: url)
            }
        } else {
            for url in urls {
                if url.pathExtension.lowercased() == "zip" {
                    uploadFolderToBackend(url: url)
                    return
                }
            }
            if let first = urls.first {
                selectedFileURL = first
                selectedFileName = first.lastPathComponent
                analyzeFile(url: first)
            }
        }
    }

    private func commitFile() {
        guard let url = selectedFileURL else {
            ingestError = "No file selected."
            return
        }
        guard url.startAccessingSecurityScopedResource() else {
            ingestError = "Permission denied for file."
            return
        }
        defer { url.stopAccessingSecurityScopedResource() }

        do {
            let data = try Data(contentsOf: url)
            isCommitting = true
            ingestError = nil

            Task {
                defer {
                    DispatchQueue.main.async { isCommitting = false }
                }
                do {
                    let boundary = UUID().uuidString
                    var request = URLRequest(url: URL(string: "http://127.0.0.1:8000/ingest/file")!)
                    request.httpMethod = "POST"
                    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

                    var bodyData = Data()
                    bodyData.append("--\(boundary)\r\n".data(using: .utf8)!)
                    bodyData.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(url.lastPathComponent)\"\r\n".data(using: .utf8)!)
                    bodyData.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
                    bodyData.append(data)
                    bodyData.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
                    request.httpBody = bodyData

                    let (responseData, response) = try await URLSession.shared.data(for: request)
                    guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                        throw URLError(.badServerResponse)
                    }
                    let result = try JSONDecoder().decode(APIFileIngestResponse.self, from: responseData)
                    await MainActor.run {
                        withAnimation {
                            commitResult = result
                            analysisResult = nil
                        }
                        if result.success {
                            Task {
                                await backendService.fetchLoreEntities(context: modelContext)
                                await backendService.fetchTemporalEvents(context: modelContext)
                            }
                        }
                    }
                } catch {
                    await MainActor.run {
                        ingestError = "Commit failed: \(error.localizedDescription)"
                    }
                }
            }
        } catch {
            ingestError = "Failed to read file: \(error.localizedDescription)"
        }
    }

    private func uploadFolderToBackend(url: URL) {
        guard url.startAccessingSecurityScopedResource() else {
            ingestError = "Permission denied for archive."
            return
        }
        defer { url.stopAccessingSecurityScopedResource() }

        do {
            let data = try Data(contentsOf: url)
            isBulkIngesting = true
            ingestError = nil

            Task {
                defer {
                    DispatchQueue.main.async { isBulkIngesting = false }
                }
                do {
                    let boundary = UUID().uuidString
                    var request = URLRequest(url: URL(string: "http://127.0.0.1:8000/ingest/folder")!)
                    request.httpMethod = "POST"
                    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

                    var bodyData = Data()
                    bodyData.append("--\(boundary)\r\n".data(using: .utf8)!)
                    bodyData.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(url.lastPathComponent)\"\r\n".data(using: .utf8)!)
                    bodyData.append("Content-Type: application/zip\r\n\r\n".data(using: .utf8)!)
                    bodyData.append(data)
                    bodyData.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
                    request.httpBody = bodyData

                    let (_, response) = try await URLSession.shared.data(for: request)
                    if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                        await backendService.fetchLoreEntities(context: modelContext)
                        await backendService.fetchTemporalEvents(context: modelContext)
                    }
                } catch {
                    await MainActor.run {
                        ingestError = "Folder upload failed: \(error.localizedDescription)"
                    }
                }
            }
        } catch {
            ingestError = "Failed to read archive: \(error.localizedDescription)"
        }
    }

    private func enumerateAndProcessFolder(url: URL) {
        guard url.startAccessingSecurityScopedResource() else {
            ingestError = "Permission denied for folder."
            return
        }
        isProcessingFolder = true
        ingestError = nil

        Task {
            defer {
                url.stopAccessingSecurityScopedResource()
                DispatchQueue.main.async { isProcessingFolder = false }
            }
            let fm = FileManager.default
            guard let enumerator = fm.enumerator(at: url, includingPropertiesForKeys: [.isRegularFileKey]) else {
                await MainActor.run { ingestError = "Failed to enumerate folder." }
                return
            }

            var allResults: [APIFileIngestResponse] = []
            while let fileURL = enumerator.nextObject() as? URL {
                let ext = fileURL.pathExtension.lowercased()
                guard ["txt", "md", "json", "csv"].contains(ext) else { continue }
                guard let data = try? Data(contentsOf: fileURL),
                      let text = String(data: data, encoding: .utf8) else { continue }
                let bodyDict: [String: Any] = ["content": text, "filename": fileURL.lastPathComponent]
                guard let bodyData = try? JSONSerialization.data(withJSONObject: bodyDict) else { continue }
                if let result: APIFileIngestResponse = try? await APIClient.shared.request(
                    path: "/ingest/file",
                    method: "POST",
                    body: bodyData
                ) {
                    allResults.append(result)
                }
            }

            await MainActor.run {
                folderResult = APIFolderIngestResponse(
                    success: true,
                    totalFiles: allResults.count,
                    totalPagesCreated: allResults.reduce(0) { $0 + $1.pagesCreated.count },
                    totalPagesUpdated: allResults.reduce(0) { $0 + $1.pagesUpdated.count },
                    totalNodesCreated: allResults.reduce(0) { $0 + $1.nodesCreated },
                    totalRelationshipsCreated: allResults.reduce(0) { $0 + $1.relationshipsCreated },
                    fileResults: allResults
                )
                uploadedFiles = allResults.flatMap { $0.pagesCreated + $0.pagesUpdated }
                Task {
                    await backendService.fetchLoreEntities(context: modelContext)
                    await backendService.fetchTemporalEvents(context: modelContext)
                }
            }
        }
    }

    private func runBulkIngestion() {
        isBulkIngesting = true
        Task {
            guard let url = URL(string: "http://127.0.0.1:8000/ingest/bulk") else {
                await MainActor.run { isBulkIngesting = false }
                return
            }

            var request = URLRequest(url: url)
            request.httpMethod = "POST"

            do {
                let (_, response) = try await URLSession.shared.data(for: request)
                if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                    await backendService.fetchLoreEntities(context: modelContext)
                    await backendService.fetchTemporalEvents(context: modelContext)
                    if !backendService.focusedEntityName.isEmpty {
                        await backendService.fetchNeighborhood(for: backendService.focusedEntityName, context: modelContext)
                    }
                }
            } catch {
                print("Failed to run bulk ingestion: \(error.localizedDescription)")
            }

            await MainActor.run {
                isBulkIngesting = false
            }
        }
    }
}

// MARK: - Annotation Adjustment Sheet

struct EditAnnotationSheet: View {
    @Bindable var entity: LoreEntity
    var onSave: (LoreEntity) -> Void

    var body: some View {
        NavigationStack {
            Form {
                Section("Properties") {
                    TextField("Name", text: $entity.name)
                    TextField("Type", text: $entity.type)
                }

                Section("Summary") {
                    TextEditor(text: $entity.summary)
                        .frame(height: 100)
                }

                Section("Manual Adjustments") {
                    VStack(alignment: .leading) {
                        Text("Confidence: \(Int(entity.confidence * 100))%")
                        Slider(value: $entity.confidence, in: 0...1)
                    }
                    TextField("User Notes (Client Wins)", text: $entity.userNotes)
                }

                Section("Sources (Union)") {
                    Text(entity.sources.joined(separator: ", "))
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                }
            }
            .navigationTitle("Modify Annotation")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        onSave(entity)
                    }
                }
            }
        }
    }
}
