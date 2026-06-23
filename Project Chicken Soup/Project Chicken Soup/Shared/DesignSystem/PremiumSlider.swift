//
//  PremiumSlider.swift
//  Project Chicken Soup
//
//  Created by mck on 6/23/26.
//

import SwiftUI

struct PremiumSlider: View {
    @Binding var value: Double
    var range: ClosedRange<Double> = 0...1
    
    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                // Background Track
                Capsule()
                    .fill(DesignConstants.dividerColor)
                    .frame(height: 6)
                
                // Active Progress Fill
                Capsule()
                    .fill(DesignConstants.systemOrange)
                    .frame(width: CGFloat((value - range.lowerBound) / (range.upperBound - range.lowerBound)) * geometry.size.width, height: 6)
                
                // Slider Thumb (Knob)
                Circle()
                    .fill(DesignConstants.cardBackground)
                    .frame(width: 16, height: 16)
                    .shadow(color: DesignConstants.glassShadowColor.opacity(0.5), radius: 3, x: 0, y: 1.5)
                    .overlay(
                        Circle()
                            .stroke(DesignConstants.systemOrangeText, lineWidth: 1.5)
                    )
                    .offset(x: CGFloat((value - range.lowerBound) / (range.upperBound - range.lowerBound)) * (geometry.size.width - 16))
                    .gesture(
                        DragGesture(minimumDistance: 0)
                            .onChanged { gesture in
                                guard geometry.size.width > 0 else { return }
                                let percentage = gesture.location.x / geometry.size.width
                                let newValue = range.lowerBound + Double(percentage) * (range.upperBound - range.lowerBound)
                                value = min(max(newValue, range.lowerBound), range.upperBound)
                            }
                    )
            }
            .frame(height: 16)
        }
        .frame(height: 16)
    }
}
