import SwiftUI

struct BudgetCardView: View {
    @Environment(AlmanacService.self) private var almanacService
    var backendService = BackendService.shared
    let onHoldReleased: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("API ENDPOINT BUDGET")
                        .font(.caption2)
                        .bold()
                        .foregroundStyle(DesignConstants.secondaryText)
                    
                    if let key = almanacService.budgetStatus?.monthKey {
                        Text("Current Cycle: \(key)")
                            .font(.subheadline)
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                    }
                }
                
                Spacer()
                
                if almanacService.isFetchingBudget {
                    ProgressView().progressViewStyle(.circular).scaleEffect(0.8)
                } else {
                    Button(action: {
                        Task { await almanacService.fetchBudgetStatus() }
                    }) {
                        Image(systemName: "arrow.clockwise")
                            .font(.subheadline)
                            .foregroundStyle(DesignConstants.systemOrange)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Refresh budget status")
                }
            }
            
            if let budget = almanacService.budgetStatus {
                let spent = budget.spentUsd
                let ceiling = budget.ceilingUsd
                let progress = ceiling > 0 ? spent / ceiling : 0.0
                
                VStack(alignment: .leading, spacing: 8) {
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Rectangle()
                                .fill(Color.gray.opacity(0.15))
                            Rectangle()
                                .fill(budget.onHold ? DesignConstants.systemRed : (progress > 0.8 ? Color.red : DesignConstants.systemOrange))
                                .frame(width: geo.size.width * CGFloat(min(progress, 1.0)))
                        }
                    }
                    .frame(height: 10)
                    .clipShape(Capsule())
                    
                    HStack {
                        Text(String(format: "$%.2f Spent", spent))
                            .font(.system(.caption, design: .monospaced))
                            .bold()
                            .foregroundStyle(DesignConstants.primaryText)
                        
                        Spacer()
                        
                        Text(String(format: "$%.2f Ceiling", ceiling))
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(DesignConstants.secondaryText)
                    }
                    
                    HStack {
                        Label("\(budget.pullsCount) pulls performed", systemImage: "network")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                        
                        Spacer()
                        
                        Text("Remaining: \(String(format: "$%.2f", budget.remainingUsd))")
                            .font(.system(.caption2, design: .monospaced))
                            .bold()
                            .foregroundStyle(budget.remainingUsd > 0 ? DesignConstants.systemGreenText : DesignConstants.systemRed)
                    }
                }
                
                if budget.onHold {
                    VStack(spacing: 12) {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundStyle(DesignConstants.systemRed)
                            Text("API SPENDING SAFETY HOLD ACTIVE")
                                .font(.caption)
                                .bold()
                                .foregroundStyle(DesignConstants.systemRed)
                        }
                        
                        Text("The monthly budget limit has been reached or triggered manual safety controls. Confirm approval to release hold.")
                            .font(.caption2)
                            .foregroundStyle(DesignConstants.secondaryText)
                            .multilineTextAlignment(.center)
                        
                        Button("Approve and Release Hold") {
                            Task {
                                let success = await almanacService.approveBudgetHold()
                                if success {
                                    onHoldReleased()
                                }
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(DesignConstants.systemRed)
                        .controlSize(.small)
                        .bold()
                    }
                    .padding()
                    .background(Color.red.opacity(0.08))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(DesignConstants.systemRed.opacity(0.3), lineWidth: 1))
                }
            } else {
                Text("Ingestion budget status unavailable. Turn on active network settings in .env.")
                    .font(.caption2)
                    .foregroundStyle(DesignConstants.secondaryText)
            }
        }
        .padding()
        .background(DesignConstants.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius))
        .overlay(RoundedRectangle(cornerRadius: DesignConstants.cardCornerRadius).stroke(DesignConstants.glassBorderColor, lineWidth: 1))
        .padding(.horizontal)
    }
}
