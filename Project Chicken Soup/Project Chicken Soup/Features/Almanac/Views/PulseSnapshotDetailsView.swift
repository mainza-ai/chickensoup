import SwiftUI

struct PulseSnapshotDetailsView: View {
    let details: [String: AnyDecodableValue]
    
    private var claims: [[String: AnyDecodableValue]] {
        if let arr = details["evidence"]?.asArray {
            return arr.compactMap { $0.asDictionary }
        }
        return []
    }
    
    var body: some View {
        List {
            Section("SNAPSHOT SUMMARY") {
                LabeledContent("Entity Name", value: details["entity_name"]?.asString ?? "")
                LabeledContent("Status", value: details["status"]?.asString ?? "")
                LabeledContent("Budget Remaining", value: String(format: "$%.2f", details["budget_remaining"]?.asDouble ?? 0.0))
            }
            
            Section("EVIDENCE CLAIMS COLLECTED (\(claims.count))") {
                if claims.isEmpty {
                    Text("No claims collected in this pulse snapshot.")
                        .font(.caption)
                        .foregroundStyle(DesignConstants.secondaryText)
                } else {
                    ForEach(0..<claims.count, id: \.self) { idx in
                        let claim = claims[idx]
                        VStack(alignment: .leading, spacing: 6) {
                            Text(claim["claim_text"]?.asString ?? "Unknown Claim")
                                .font(.subheadline)
                                .bold()
                                .foregroundStyle(DesignConstants.primaryText)
                            
                            HStack {
                                if let platform = claim["source_platform"]?.asString {
                                    Text(platform.uppercased())
                                        .font(.caption2)
                                        .bold()
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(DesignConstants.controlBackground)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                        .clipShape(Capsule())
                                }
                                
                                if let count = claim["engagement_count"]?.asInt {
                                    Text("Engagement: \(count)")
                                        .font(.caption2)
                                        .foregroundStyle(DesignConstants.secondaryText)
                                }
                                
                                Spacer()
                                
                                if let url = claim["url"]?.asString, let u = URL(string: url) {
                                    Link(destination: u) {
                                        Label("Source Link", systemImage: "link")
                                            .font(.caption2)
                                    }
                                }
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
    }
}
