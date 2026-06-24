//
//  DataIngestionView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData
import UniformTypeIdentifiers

struct DataIngestionView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \LoreEntity.name) private var localEntities: [LoreEntity]
    @Query(sort: \TemporalEvent.timestamp) private var localEvents: [TemporalEvent]
    
    @ObservedObject var syncService = SyncService.shared
    @ObservedObject var backendService = BackendService.shared
    
    // States for File Upload Simulation
    @State private var isDraggingOver = false
    @State private var uploadedFiles: [String] = []
    @State private var isExtracting = false
    @State private var isBulkIngesting = false
    
    // AI Inferred Preview Entities
    @State private var extractedEntities: [LoreEntity] = []
    @State private var selectedEntityForEdit: LoreEntity? = nil
    
    // UI layout controls
    @Namespace private var animationNamespace
    
    private var averageConfidence: Double {
        localEntities.isEmpty ? 0.0 : localEntities.map { $0.confidence }.reduce(0.0, +) / Double(localEntities.count)
    }
    
    var body: some View {
        ScrollView {
            VStack(spacing: DesignConstants.loosePadding) {
                // Quality Dashboard / Stats Row
                statsDashboard
                    .padding(.horizontal)
                
                // File Drop Target Area
                dropTargetView
                    .padding(.horizontal)
                
                // AI Entity Extraction Preview Layout
                if isExtracting {
                    loadingSkeletonView
                        .padding(.horizontal)
                } else if !extractedEntities.isEmpty {
                    extractionPreviewView
                        .padding(.horizontal)
                }
                
                // Ingested Local Entities List
                localIngestOverview
                    .padding(.horizontal)
            }
            .padding(.vertical, DesignConstants.standardPadding)
        }
        .background(DesignConstants.warmBackground.ignoresSafeArea())
        .navigationTitle("Data Ingest")
        .sheet(item: $selectedEntityForEdit) { entity in
            EditAnnotationSheet(entity: entity) { updatedEntity in
                // Save edit and sync to background service
                syncService.queueSync(entityId: updatedEntity.id, type: "LoreEntity", action: "update")
                selectedEntityForEdit = nil
            }
        }
    }
    
    // MARK: - Quality & Metadata Statistics Dashboard
    private var statsDashboard: some View {
        VStack(alignment: .leading, spacing: DesignConstants.compactPadding) {
            Text("INGEST METRICS & QUALITY")
                .font(.footnote)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.secondaryText)
                .accessibilityAddTraits(.isHeader)
            
            HStack(spacing: DesignConstants.standardPadding) {
                // Quality Metric
                VStack(alignment: .leading, spacing: 4) {
                    Text("Avg Confidence")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                    Text(String(format: "%.1f%%", averageConfidence * 100))
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundStyle(averageConfidence > 0.9 ? DesignConstants.systemGreenText : DesignConstants.systemOrangeText)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(DesignConstants.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
                .accessibilityElement(children: .combine)
                .accessibilityLabel("Average extraction confidence is \(Int(averageConfidence * 100)) percent")
                
                // Total Ingested
                VStack(alignment: .leading, spacing: 4) {
                    Text("Total Entities")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                    Text("\(localEntities.count)")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundStyle(DesignConstants.primaryText)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(DesignConstants.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
                .accessibilityElement(children: .combine)
                .accessibilityLabel("Total ingested entities is \(localEntities.count)")
                
                // Sync status
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
        }
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
            
            Text("Drag & Drop Spacetime Logs")
                .font(.headline)
                .foregroundStyle(DesignConstants.primaryText)
            
            Text("Supports TXT, JSON, or CSV raw intel reports")
                .font(.caption)
                .foregroundStyle(DesignConstants.secondaryText)
            
            HStack(spacing: 12) {
                Button("Browse Files", systemImage: "folder.fill") {
                    simulateFileSelection()
                }
                .buttonStyle(.bordered)
                .disabled(isBulkIngesting)
                .accessibilityLabel("Browse local files to ingest data")
                
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
            // Handle drops in SwiftUI
            simulateFileSelection()
            return true
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("File drop area. Drag and drop intel files here.")
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
                        Text("Simulated Entity Name Placeholder")
                            .font(.body)
                        Text("Category: Person/Place/Object")
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
    
    // MARK: - AI Inferred Previews
    private var extractionPreviewView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("AI EXTRACTED ENTITIES (PREVIEW)")
                    .font(.footnote)
                    .fontWeight(.bold)
                    .foregroundStyle(DesignConstants.secondaryText)
                
                Spacer()
                
                Button("Approve and Commit All") {
                    withAnimation(DesignConstants.hoverAnimation) {
                        for entity in extractedEntities {
                            modelContext.insert(entity)
                            syncService.queueSync(entityId: entity.id, type: "LoreEntity", action: "create")
                        }
                        extractedEntities.removeAll()
                    }
                }
                .font(.caption)
                .buttonStyle(.bordered)
                .tint(DesignConstants.systemGreen)
                .accessibilityLabel("Commit all extracted entities to the timeline lore graph")
            }
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: DesignConstants.standardPadding) {
                    ForEach(extractedEntities) { entity in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(entity.name)
                                    .font(.headline)
                                    .foregroundStyle(DesignConstants.primaryText)
                                Spacer()
                                Text(entity.type)
                                    .font(.caption2)
                                    .fontWeight(.bold)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(DesignConstants.systemOrange.opacity(0.15))
                                    .foregroundStyle(DesignConstants.systemOrangeText)
                                    .clipShape(Capsule())
                            }
                            
                            Text(entity.summary)
                                .font(.caption)
                                .foregroundStyle(DesignConstants.secondaryText)
                                .lineLimit(3)
                            
                            HStack {
                                Image(systemName: "percent")
                                    .font(.caption)
                                Text(String(format: "%.0f%% Confidence", entity.confidence * 100))
                                    .font(.caption)
                            }
                            .foregroundStyle(entity.confidence > 0.9 ? DesignConstants.systemGreenText : DesignConstants.systemOrangeText)
                            
                            HStack {
                                Button(action: {
                                    selectedEntityForEdit = entity
                                }) {
                                    Label("Edit Intel", systemImage: "pencil.line")
                                        .font(.caption2)
                                }
                                .buttonStyle(.bordered)
                                
                                Spacer()
                                
                                Button(action: {
                                    withAnimation {
                                        extractedEntities.removeAll { $0.id == entity.id }
                                    }
                                }) {
                                    Image(systemName: "trash")
                                        .foregroundStyle(DesignConstants.systemRed)
                                        .font(.caption)
                                }
                                .accessibilityLabel("Discard \(entity.name)")
                            }
                        }
                        .frame(width: 220, height: 180)
                        .padding()
                        .background(DesignConstants.cardBackground)
                        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                        .shadow(color: DesignConstants.glassShadowColor, radius: 6, y: 3)
                        .matchedGeometryEffect(id: entity.id, in: animationNamespace)
                    }
                }
                .padding(.vertical, 6)
            }
        }
    }
    
    // MARK: - Ingested Overview list
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
    
    // MARK: - Actions
    private func simulateFileSelection() {
        isExtracting = true
        uploadedFiles = ["spacetime_log_alpha.txt", "varginha_intel_brief.json"]
        
        Task {
            try? await Task.sleep(for: .seconds(2.0))
            await MainActor.run {
                withAnimation(DesignConstants.hoverAnimation) {
                    isExtracting = false
                    extractedEntities = [
                        LoreEntity(name: "Tic Tac Craft", type: "Object", summary: "Oblong white aerial object reported by Commander David Fravor off Nimitz carrier strike group.", confidence: 0.97, source: "USS Nimitz logs", userNotes: "Investigate gravity distortion metric if possible"),
                        LoreEntity(name: "Cmdr Fravor", type: "Person", summary: "Navy pilot witness who engaged Tic Tac UFO during mock combat training.", confidence: 0.94, source: "Senate hearings", userNotes: "Firsthand witness, high credibility"),
                        LoreEntity(name: "Capistrano Site", type: "Place", summary: "Underground test facility associated with back-engineered propulsion systems.", confidence: 0.84, source: "Bob Lazar diary", userNotes: "")
                    ]
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
                    // Sync backend state into SwiftData
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
