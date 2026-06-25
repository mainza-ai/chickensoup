//
//  AdvancedTimelineFilterView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import SwiftUI
import SwiftData

struct FilterPreset: Identifiable, Codable, Equatable {
    var id = UUID()
    var name: String
    var minConfidence: Double
    var selectedTypes: [String]
}

struct AdvancedTimelineFilterView: View {
    @Binding var minConfidence: Double
    @Binding var selectedTypes: Set<String>
    @Binding var activeBranchId: UUID?
    
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @Query private var branches: [TimelineBranch]
    
    private var isCompact: Bool { horizontalSizeClass == .compact }
    
    // Saved presets stored in AppStorage for persistence
    @State private var presets: [FilterPreset] = []
    @State private var newPresetName = ""
    @State private var showSaveDialog = false
    
    let allTypes = ["crash", "testimony", "anomaly", "theory"]
    
    var body: some View {
        VStack(alignment: .leading, spacing: DesignConstants.standardPadding) {
            HStack {
                Text("Advanced Filters")
                    .font(.headline)
                    .bold()
                Spacer()
                
                // Clear button
                Button("Reset") {
                    withAnimation {
                        minConfidence = 0.0
                        selectedTypes = Set(allTypes)
                        activeBranchId = branches.first(where: { $0.isActive })?.id ?? branches.first?.id
                    }
                }
                .buttonStyle(.plain)
                .font(.caption)
                .foregroundStyle(DesignConstants.systemOrangeText)
            }
            
            Divider()
            
            // 1. Confidence Slider
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("Minimum Confidence")
                        .font(.subheadline)
                        .foregroundStyle(DesignConstants.primaryText)
                    Spacer()
                    Text(minConfidence, format: .percent.precision(.fractionLength(0)))
                        .font(.system(.subheadline, design: .monospaced))
                        .foregroundStyle(DesignConstants.secondaryText)
                }
                Slider(value: $minConfidence, in: 0...1.0)
                    .tint(DesignConstants.systemOrange)
            }
            
            // 2. Event Type Tag Selection
            VStack(alignment: .leading, spacing: 8) {
                Text("Event Classifications")
                    .font(.subheadline)
                    .foregroundStyle(DesignConstants.primaryText)
                
                FlowLayout(spacing: 8) {
                    ForEach(allTypes, id: \.self) { type in
                        let isSelected = selectedTypes.contains(type)
                        Button {
                            withAnimation(.spring(duration: 0.2)) {
                                if isSelected {
                                    if selectedTypes.count > 1 {
                                        selectedTypes.remove(type)
                                    }
                                } else {
                                    selectedTypes.insert(type)
                                }
                            }
                        } label: {
                            Text(type.capitalized)
                                .font(.caption)
                                .bold()
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(
                                    isSelected ? DesignConstants.systemOrange : Color.secondary.opacity(0.1),
                                    in: Capsule()
                                )
                                .foregroundStyle(isSelected ? .white : .primary)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            
            // 3. Active Branch Setting
            VStack(alignment: .leading, spacing: 8) {
                Text("Timeline Branch")
                    .font(.subheadline)
                    .foregroundStyle(DesignConstants.primaryText)
                
                Picker("Branch", selection: $activeBranchId) {
                    Text("All Branches").tag(UUID?.none)
                    ForEach(branches) { branch in
                        Text(branch.name).tag(UUID?.init(branch.id))
                    }
                }
                .pickerStyle(.menu)
            }
            
            Divider()
            
            // 4. Saved Presets Section
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Filter Presets")
                        .font(.subheadline)
                        .bold()
                    Spacer()
                    Button {
                        showSaveDialog = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .foregroundStyle(DesignConstants.systemOrangeText)
                    }
                    .buttonStyle(.plain)
                }
                
                if presets.isEmpty {
                    Text("No saved presets. Create one to store current filters.")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                } else {
                    ScrollView(.horizontal) {
                        HStack(spacing: 8) {
                            ForEach(presets) { preset in
                                Button {
                                    withAnimation {
                                        minConfidence = preset.minConfidence
                                        selectedTypes = Set(preset.selectedTypes)
                                    }
                                } label: {
                                    HStack(spacing: 4) {
                                        Text(preset.name)
                                            .font(.caption)
                                            .bold()
                                        
                                        Button("Delete \"\(preset.name)\"", systemImage: "xmark") {
                                            presets.removeAll { $0.id == preset.id }
                                            savePresetsToStorage()
                                        }
                                        .buttonStyle(.plain)
                                        .labelStyle(.iconOnly)
                                        .font(.caption)
                                    }
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(DesignConstants.systemOrange.opacity(0.1), in: RoundedRectangle(cornerRadius: 6))
                                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(DesignConstants.systemOrange.opacity(0.3), lineWidth: 1))
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                    .scrollIndicators(.hidden)
                }
            }
        }
        .padding(DesignConstants.standardPadding)
        .background(DesignConstants.panelBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(DesignConstants.dividerColor, lineWidth: 1))
        .onAppear {
            loadPresetsFromStorage()
        }
        .sheet(isPresented: $showSaveDialog) {
            VStack(spacing: 16) {
                Text("Save Filter Preset")
                    .font(.headline)
                
                TextField("Preset Name", text: $newPresetName)
                    .textFieldStyle(.roundedBorder)
                    .padding(.horizontal)
                
                HStack {
                    Button("Cancel") {
                        showSaveDialog = false
                        newPresetName = ""
                    }
                    .buttonStyle(.bordered)
                    
                    Button("Save") {
                        guard !newPresetName.isEmpty else { return }
                        let newPreset = FilterPreset(
                            name: newPresetName,
                            minConfidence: minConfidence,
                            selectedTypes: Array(selectedTypes)
                        )
                        presets.append(newPreset)
                        savePresetsToStorage()
                        newPresetName = ""
                        showSaveDialog = false
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(DesignConstants.systemOrange)
                }
            }
            .padding()
            .frame(width: 250, height: 160)
        }
    }
    
    private func loadPresetsFromStorage() {
        if let data = UserDefaults.standard.data(forKey: "TimelineFilterPresets"),
           let decoded = try? JSONDecoder().decode([FilterPreset].self, from: data) {
            self.presets = decoded
        } else {
            // Default seed presets
            self.presets = [
                FilterPreset(name: "High Confidence", minConfidence: 0.90, selectedTypes: ["crash", "testimony", "anomaly", "theory"]),
                FilterPreset(name: "Physical Evidence", minConfidence: 0.50, selectedTypes: ["crash", "anomaly"])
            ]
        }
    }
    
    private func savePresetsToStorage() {
        if let encoded = try? JSONEncoder().encode(presets) {
            UserDefaults.standard.set(encoded, forKey: "TimelineFilterPresets")
        }
    }
}

// Simple FlowLayout helper to wrap children horizontally
struct FlowLayout: Layout {
    var spacing: CGFloat
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let sizes = subviews.map { $0.sizeThatFits(.unspecified) }
        let width: CGFloat = proposal.width ?? 300
        var height: CGFloat = 0
        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var maxRowHeight: CGFloat = 0
        
        for size in sizes {
            if currentX + size.width > width {
                currentX = 0
                currentY += maxRowHeight + spacing
                maxRowHeight = 0
            }
            maxRowHeight = max(maxRowHeight, size.height)
            currentX += size.width + spacing
        }
        height = currentY + maxRowHeight
        return CGSize(width: width, height: height)
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let sizes = subviews.map { $0.sizeThatFits(.unspecified) }
        var currentX: CGFloat = bounds.minX
        var currentY: CGFloat = bounds.minY
        var maxRowHeight: CGFloat = 0
        
        for (index, subview) in subviews.enumerated() {
            let size = sizes[index]
            if currentX + size.width > bounds.maxX {
                currentX = bounds.minX
                currentY += maxRowHeight + spacing
                maxRowHeight = 0
            }
            subview.place(at: CGPoint(x: currentX, y: currentY), proposal: .unspecified)
            maxRowHeight = max(maxRowHeight, size.height)
            currentX += size.width + spacing
        }
    }
}
