import SwiftUI
import SwiftData

struct LoreRepositoryView: View {
    @Query(sort: \LoreEntity.name) private var localEntities: [LoreEntity]
    var backendService = BackendService.shared

    @State private var searchText = ""
    @State private var typeFilter: String? = nil
    @State private var sortOrder: SortOrder = .name
    @State private var entityToDelete: LoreEntity? = nil
    @State private var showDeleteConfirmation = false
    @State private var selectedEntityForEdit: LoreEntity? = nil
    @State private var displayLimit = 50

    @Environment(\.modelContext) private var modelContext

    enum SortOrder: String, CaseIterable {
        case name = "Name"
        case type = "Type"
        case confidence = "Confidence"
        case source = "Source"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            header
            if !localEntities.isEmpty {
                searchBar
                filterChips
            }
            if localEntities.isEmpty {
                emptyState
            } else if filteredEntities.isEmpty {
                noMatchState
            } else {
                entityList
            }
        }
        .onChange(of: searchText) { _, _ in displayLimit = 50 }
        .onChange(of: typeFilter) { _, _ in displayLimit = 50 }
        .onChange(of: sortOrder) { _, _ in displayLimit = 50 }
        .sheet(item: $selectedEntityForEdit) { entity in
            EditAnnotationSheet(entity: entity) { updatedEntity in
                selectedEntityForEdit = nil
            }
        }
        .alert("Delete '\(entityToDelete?.name ?? "")'?", isPresented: $showDeleteConfirmation, presenting: entityToDelete) { entity in
            Button("Cancel", role: .cancel) { entityToDelete = nil }
            Button("Delete", role: .destructive) {
                Task {
                    modelContext.delete(entity)
                    try? modelContext.save()
                    await backendService.deleteLoreEntity(name: entity.name)
                }
            }
        } message: { entity in
            Text("This removes the entity from your local store and the Neo4j knowledge graph.")
        }
    }

    private var header: some View {
        HStack {
            Text("LORE REPOSITORY (\(filteredEntities.count))")
                .font(.footnote)
                .fontWeight(.bold)
                .foregroundStyle(DesignConstants.secondaryText)
            Spacer()
            Menu {
                ForEach(SortOrder.allCases, id: \.self) { order in
                    Button {
                        sortOrder = order
                    } label: {
                        HStack {
                            Text(order.rawValue)
                            if sortOrder == order {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                Label("Sort", systemImage: "arrow.up.arrow.down")
                    .font(.caption)
                    .foregroundStyle(DesignConstants.systemBlue)
            }
            Button {
                Task {
                    await backendService.fetchLoreEntities(context: modelContext)
                }
            } label: {
                Label("Refresh", systemImage: "arrow.clockwise")
                    .font(.caption)
                    .foregroundStyle(DesignConstants.systemBlue)
            }
        }
    }

    private var searchBar: some View {
        HStack(spacing: 6) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(DesignConstants.secondaryText)
                .font(.caption)
            TextField("Search entities...", text: $searchText)
                .textFieldStyle(.plain)
                .font(.caption)
            if !searchText.isEmpty {
                Button {
                    searchText = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(DesignConstants.secondaryText)
                        .font(.caption)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(10)
        .background(DesignConstants.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var filterChips: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                chip("All", type: nil)
                chip("Person", type: "Person")
                chip("Place", type: "Place")
                chip("Concept", type: "Concept")
                chip("Object", type: "Object")
                chip("Project", type: "Project")
                chip("Event", type: "Event")
                chip("Entity", type: "Entity")
            }
        }
    }

    private func chip(_ label: String, type: String?) -> some View {
        Button(label) {
            typeFilter = typeFilter == type ? nil : type
        }
        .font(.caption2)
        .fontWeight(.bold)
        .padding(.horizontal, 8)
        .padding(.vertical, 3)
        .background(typeFilter == type ? DesignConstants.systemBlue.opacity(0.2) : DesignConstants.cardBackground)
        .foregroundStyle(typeFilter == type ? DesignConstants.systemBlue : DesignConstants.secondaryText)
        .clipShape(Capsule())
    }

    private var emptyState: some View {
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
    }

    private var noMatchState: some View {
        VStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .font(.title2)
                .foregroundStyle(DesignConstants.secondaryText)
            Text("No entities match your search.")
                .font(.subheadline)
                .foregroundStyle(DesignConstants.secondaryText)
        }
        .frame(maxWidth: .infinity)
        .padding()
    }

    private var entityList: some View {
        LazyVStack(spacing: DesignConstants.compactPadding) {
            ForEach(paginatedEntities) { entity in
                EntityRowView(entity: entity)
                    .onTapGesture {
                        selectedEntityForEdit = entity
                    }
                    .contextMenu {
                        Button { selectedEntityForEdit = entity } label: {
                            Label("Edit", systemImage: "pencil")
                        }
                        Button(role: .destructive) {
                            entityToDelete = entity
                            showDeleteConfirmation = true
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                    }
            }
            if hasMoreEntities {
                Button("Load More (\(filteredEntities.count - displayLimit) remaining)", systemImage: "ellipsis.circle") {
                    displayLimit += 50
                }
                .font(.caption)
                .buttonStyle(.bordered)
                .tint(DesignConstants.systemBlue)
                .padding(.top, 4)
            }
        }
    }

    private var hasMoreEntities: Bool {
        filteredEntities.count > displayLimit
    }

    private var paginatedEntities: [LoreEntity] {
        Array(filteredEntities.prefix(displayLimit))
    }

    private var filteredEntities: [LoreEntity] {
        var result = localEntities.filter { entity in
            let matchesSearch = searchText.isEmpty || entity.name.localizedCaseInsensitiveContains(searchText)
            let matchesType = typeFilter == nil || entity.type == typeFilter
            return matchesSearch && matchesType
        }
        switch sortOrder {
        case .name: result.sort { $0.name.localizedCompare($1.name) == .orderedAscending }
        case .type: result.sort { $0.type < $1.type }
        case .confidence: result.sort { $0.confidence > $1.confidence }
        case .source: result.sort { $0.source < $1.source }
        }
        return result
    }
}

struct EntityRowView: View {
    let entity: LoreEntity

    var body: some View {
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
                    .background(typeColor(entity.type).opacity(0.15))
                    .foregroundStyle(typeColor(entity.type))
                    .clipShape(Capsule())
                Text("\(Int(entity.confidence * 100))%")
                    .font(.caption2)
                    .foregroundStyle(entity.confidence > 0.9 ? DesignConstants.systemGreenText : DesignConstants.systemOrangeText)
            }
        }
        .padding()
        .background(DesignConstants.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
        .shadow(color: DesignConstants.glassShadowColor, radius: 4, y: 2)
    }

    private func typeColor(_ type: String) -> Color {
        switch type {
        case "Person": return DesignConstants.systemBlue
        case "Place": return DesignConstants.systemGreenText
        case "Concept": return DesignConstants.systemPurple
        case "Object": return DesignConstants.systemOrangeText
        case "Project": return DesignConstants.systemRed
        case "Event": return DesignConstants.systemOrange
        case "Entity": return DesignConstants.secondaryText
        default: return DesignConstants.secondaryText
        }
    }
}
