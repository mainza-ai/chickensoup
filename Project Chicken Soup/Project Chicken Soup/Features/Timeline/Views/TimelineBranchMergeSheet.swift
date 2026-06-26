import SwiftUI

struct TimelineBranchMergeSheet: View {
    @Environment(\.dismiss) private var dismiss
    
    // Conflicting nodes state parameters
    let nodeName: String
    
    @State private var selectedTitle: String
    @State private var selectedDescription: String
    @State private var selectedDate: Date
    @State private var selectedConfidence: Double
    @State private var selectedSource: String
    
    // Constant values for comparison
    let localTitle: String
    let remoteTitle: String
    
    let localDescription: String
    let remoteDescription: String
    
    let localDate: Date
    let remoteDate: Date
    
    let localConfidence: Double
    let remoteConfidence: Double
    
    let localSource: String
    let remoteSource: String
    
    var onResolve: (String, String, Date, Double, String) -> Void
    
    init(
        nodeName: String,
        localTitle: String,
        remoteTitle: String,
        localDescription: String,
        remoteDescription: String,
        localDate: Date,
        remoteDate: Date,
        localConfidence: Double,
        remoteConfidence: Double,
        localSource: String,
        remoteSource: String,
        onResolve: @escaping (String, String, Date, Double, String) -> Void
    ) {
        self.nodeName = nodeName
        self.localTitle = localTitle
        self.remoteTitle = remoteTitle
        self.localDescription = localDescription
        self.remoteDescription = remoteDescription
        self.localDate = localDate
        self.remoteDate = remoteDate
        self.localConfidence = localConfidence
        self.remoteConfidence = remoteConfidence
        self.localSource = localSource
        self.remoteSource = remoteSource
        self.onResolve = onResolve
        
        // Default to local selections initially
        _selectedTitle = State(initialValue: localTitle)
        _selectedDescription = State(initialValue: localDescription)
        _selectedDate = State(initialValue: localDate)
        _selectedConfidence = State(initialValue: localConfidence)
        _selectedSource = State(initialValue: localSource)
    }
    
    var body: some View {
        ScrollView {
            VStack(spacing: DesignConstants.loosePadding) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: "arrow.triangle.2.circlepath.camera.fill")
                        .font(.system(size: 38))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [DesignConstants.systemOrange, .purple],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .padding(.bottom, 8)
                    
                    Text("Resolve Spacetime Conflict")
                        .font(.title3)
                        .bold()
                        .foregroundStyle(DesignConstants.primaryText)
                    
                    Text("Timeline deviations detected for '\(nodeName)'. Select which parameters to sync into Universe Prime.")
                        .font(.subheadline)
                        .foregroundStyle(DesignConstants.secondaryText)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
                .padding(.top, DesignConstants.loosePadding)
                
                // Fields Grid
                VStack(spacing: DesignConstants.standardPadding) {
                    // Field 1: Title
                    conflictRow(
                        fieldName: "Event Title",
                        local: localTitle,
                        remote: remoteTitle,
                        selected: $selectedTitle
                    )
                    
                    Divider()
                        .background(DesignConstants.dividerColor)
                    
                    // Field 2: Description
                    conflictRow(
                        fieldName: "Description",
                        local: localDescription,
                        remote: remoteDescription,
                        selected: $selectedDescription
                    )
                    
                    Divider()
                        .background(DesignConstants.dividerColor)
                    
                    // Field 3: Date
                    conflictRow(
                        fieldName: "Temporal Coordinate",
                        local: localDate,
                        remote: remoteDate,
                        selected: $selectedDate,
                        format: { date in
                            date.formatted(date: .abbreviated, time: .omitted)
                        }
                    )
                    
                    Divider()
                        .background(DesignConstants.dividerColor)
                    
                    // Field 4: Confidence
                    conflictRow(
                        fieldName: "Field Fidelity",
                        local: localConfidence,
                        remote: remoteConfidence,
                        selected: $selectedConfidence,
                        format: { val in String(format: "%.0f%%", val * 100) }
                    )
                    
                    Divider()
                        .background(DesignConstants.dividerColor)
                    
                    // Field 5: Source
                    conflictRow(
                        fieldName: "Information Source",
                        local: localSource,
                        remote: remoteSource,
                        selected: $selectedSource
                    )
                }
                .padding(DesignConstants.standardPadding)
                .background(DesignConstants.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
                .overlay(
                    RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius)
                        .stroke(DesignConstants.glassBorderColor, lineWidth: 1)
                )
                .padding(.horizontal)
                
                // Merged Preview
                VStack(alignment: .leading, spacing: 8) {
                    Text("RESOLVED PREVIEW")
                        .font(.caption2)
                        .bold()
                        .foregroundStyle(DesignConstants.secondaryText)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(selectedTitle)
                                .font(.headline)
                                .foregroundStyle(DesignConstants.primaryText)
                            Spacer()
                            Text(String(format: "%.0f%%", selectedConfidence * 100))
                                .font(.caption)
                                .bold()
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(DesignConstants.systemOrange.opacity(0.15), in: Capsule())
                                .foregroundStyle(DesignConstants.systemOrangeText)
                        }
                        
                        Text(selectedDescription)
                            .font(.caption)
                            .foregroundStyle(DesignConstants.secondaryText)
                        
                        HStack {
                            Label(formattedDate(selectedDate), systemImage: "calendar")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text("Source: \(selectedSource)")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.top, 4)
                    }
                    .padding(14)
                    .background(Color.orange.opacity(0.04))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(DesignConstants.systemOrange.opacity(0.3), lineWidth: 1)
                    )
                }
                .padding(.horizontal)
                
                // Confirm Action Button
                Button(action: {
                    onResolve(selectedTitle, selectedDescription, selectedDate, selectedConfidence, selectedSource)
                    dismiss()
                }) {
                    Text("Confirm Merge & Commit")
                        .font(.headline)
                        .bold()
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(
                            LinearGradient(
                                colors: [DesignConstants.systemOrange, .purple],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.buttonCornerRadius))
                }
                .buttonStyle(.plain)
                .padding(.horizontal)
                .padding(.bottom, DesignConstants.loosePadding)
            }
        }
        .background(DesignConstants.warmBackground)
        .navigationTitle("Timeline Merge Conflicts")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }
    
    @ViewBuilder
    private func conflictRow<Value: Equatable>(
        fieldName: String,
        local: Value,
        remote: Value,
        selected: Binding<Value>,
        format: @escaping (Value) -> String = { "\($0)" }
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(fieldName)
                .font(.caption)
                .bold()
                .foregroundStyle(DesignConstants.systemOrangeText)
            
            HStack(spacing: 12) {
                // Local Choice card
                Button(action: {
                    withAnimation(DesignConstants.hoverAnimation) {
                        selected.wrappedValue = local
                    }
                }) {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text("LOCAL VERSION")
                                .font(.system(size: 9, weight: .bold))
                                .foregroundStyle(.secondary)
                            Spacer()
                            if selected.wrappedValue == local {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(DesignConstants.systemOrange)
                            }
                        }
                        
                        Text(format(local))
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                            .multilineTextAlignment(.leading)
                    }
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(selected.wrappedValue == local ? DesignConstants.controlBackground : Color.clear)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(selected.wrappedValue == local ? DesignConstants.systemOrange : DesignConstants.dividerColor, lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)
                
                // Remote Choice card
                Button(action: {
                    withAnimation(DesignConstants.hoverAnimation) {
                        selected.wrappedValue = remote
                    }
                }) {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text("REMOTE VERSION")
                                .font(.system(size: 9, weight: .bold))
                                .foregroundStyle(.secondary)
                            Spacer()
                            if selected.wrappedValue == remote {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(.purple)
                            }
                        }
                        
                        Text(format(remote))
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.primaryText)
                            .multilineTextAlignment(.leading)
                    }
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(selected.wrappedValue == remote ? DesignConstants.controlBackground : Color.clear)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(selected.wrappedValue == remote ? .purple : DesignConstants.dividerColor, lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }
    
    private func formattedDate(_ date: Date) -> String {
        date.formatted(date: .abbreviated, time: .omitted)
    }
}

// Preview Mock Setup
#Preview {
    NavigationStack {
        TimelineBranchMergeSheet(
            nodeName: "Magenta UFO Recovery",
            localTitle: "Magenta UFO Crash Recovery",
            remoteTitle: "Magenta Secret Cabinet Recovery",
            localDescription: "A circular flying craft crash-landed in northern Italy, recovered by Mussolini's secret cabinet.",
            remoteDescription: "A massive metallic saucer-shaped craft was retrieved by Mussolini's secret RS/33 program in June 1933.",
            localDate: Date(),
            remoteDate: Date().addingTimeInterval(3600*24*15),
            localConfidence: 0.94,
            remoteConfidence: 0.97,
            localSource: "Mussolini Archives",
            remoteSource: "Italian Defense Dept Intel",
            onResolve: { _, _, _, _, _ in }
        )
    }
}
