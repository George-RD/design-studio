import React from "react";
import {
  AbsoluteFill,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";

const COLORS = {
  bg: "#FAFAFA",
  ink: "#0A0A0A",
  accent: "#FF3D00",
  muted: "#555452",
  rule: "#E0E0E0",
  deep: "#111111",
  paper: "#FAFAFA",
};

// Simple Scene container with common layout grid
const SceneContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        color: COLORS.ink,
        fontFamily: "Manrope, sans-serif",
        padding: "90px 120px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        boxSizing: "border-box",
      }}
    >
      {/* Decorative Grid Lines to match the engineering portfolio aesthetic */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: "none",
          border: `1px solid ${COLORS.rule}`,
          margin: "60px",
          zIndex: 0,
        }}
      />
      <div style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", height: "100%", justifyContent: "space-between" }}>
        {children}
      </div>
    </AbsoluteFill>
  );
};

export const PromoVideo: React.FC = () => {
  return (
    <AbsoluteFill>
      {/* Scene 1: Title (0s - 3s) */}
      <Sequence from={0} durationInFrames={180}>
        <TitleScene />
      </Sequence>

      {/* Scene 2: The Problem (3s - 8s) */}
      <Sequence from={180} durationInFrames={300}>
        <ProblemScene />
      </Sequence>

      {/* Scene 3: Solution - 4-Agent Split (8s - 14s) */}
      <Sequence from={480} durationInFrames={360}>
        <SolutionScene />
      </Sequence>

      {/* Scene 4: Scoring Rubric (14s - 19s) */}
      <Sequence from={840} durationInFrames={300}>
        <ScoringScene />
      </Sequence>

      {/* Scene 5: CTA (19s - 23s) */}
      <Sequence from={1140} durationInFrames={240}>
        <CTAScene />
      </Sequence>
    </AbsoluteFill>
  );
};

// Scene 1: Title
const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({
    frame,
    fps,
    config: { damping: 14 },
  });

  const fade = interpolate(frame, [150, 180], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <SceneContainer>
      <div style={{ opacity: fade, display: "flex", flexDirection: "column", height: "100%", justifyContent: "center" }}>
        {/* Monospace Version tag */}
        <div style={{ fontFamily: "Space Mono, monospace", fontSize: "30px", color: COLORS.accent, marginBottom: "30px" }}>
          VERSION 1.0.0
        </div>

        {/* Large Bold Serif Title */}
        <h1
          style={{
            fontFamily: "Fraunces, serif",
            fontSize: "135px",
            fontWeight: 800,
            lineHeight: 1.0,
            letterSpacing: "-0.02em",
            margin: "0 0 36px 0",
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.95, 1])})`,
            opacity: titleSpring,
          }}
        >
          Design Studio
        </h1>

        {/* Brand Tagline */}
        <p
          style={{
            fontSize: "42px",
            color: COLORS.muted,
            maxWidth: "1080px",
            lineHeight: 1.5,
            margin: 0,
            opacity: spring({ frame: frame - 20, fps, config: { damping: 12 } }),
          }}
        >
          A multi-agent design system for Claude Code that defeats code-anchoring bias to produce distinctive frontends.
        </p>
      </div>
    </SceneContainer>
  );
};

// Scene 2: The Problem
const ProblemScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps });
  const listSpring1 = spring({ frame: frame - 30, fps });
  const listSpring2 = spring({ frame: frame - 60, fps });

  const fade = interpolate(frame, [270, 300], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <SceneContainer>
      <div style={{ opacity: fade, display: "flex", flexDirection: "column", height: "100%", justifyContent: "center" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "90px", alignItems: "center" }}>
          <div>
            <div style={{ fontFamily: "Space Mono, monospace", fontSize: "24px", color: COLORS.accent, marginBottom: "24px" }}>
              THE OBSTACLE
            </div>
            <h2
              style={{
                fontFamily: "Fraunces, serif",
                fontSize: "84px",
                fontWeight: 700,
                lineHeight: 1.1,
                margin: "0 0 30px 0",
                opacity: titleSpring,
              }}
            >
              Why does AI layout look identical?
            </h2>
            <p style={{ fontSize: "30px", color: COLORS.muted, lineHeight: 1.6, margin: 0, opacity: titleSpring }}>
              When a developer model views its own code before designing, it gets anchored. It tweaks borders and padding instead of reimagining layout.
            </p>
          </div>

          <div style={{ borderLeft: `3px solid ${COLORS.accent}`, paddingLeft: "60px" }}>
            <div style={{ opacity: listSpring1, transform: `translateY(${interpolate(listSpring1, [0, 1], [30, 0])}px)`, marginBottom: "60px" }}>
              <div style={{ fontSize: "21px", fontFamily: "Space Mono, monospace", color: COLORS.muted, marginBottom: "12px" }}>
                CONVENTIONAL AI REDESIGN
              </div>
              <div style={{ fontSize: "42px", fontFamily: "Fraunces, serif", fontWeight: 700 }}>
                Originality capped at 4/10
              </div>
              <div style={{ width: "100%", height: "12px", backgroundColor: COLORS.rule, marginTop: "18px", borderRadius: "6px", overflow: "hidden" }}>
                <div style={{ width: "40%", height: "100%", backgroundColor: COLORS.muted }} />
              </div>
            </div>

            <div style={{ opacity: listSpring2, transform: `translateY(${interpolate(listSpring2, [0, 1], [30, 0])}px)` }}>
              <div style={{ fontSize: "21px", fontFamily: "Space Mono, monospace", color: COLORS.accent, marginBottom: "12px" }}>
                DESIGN STUDIO METHODOLOGY
              </div>
              <div style={{ fontSize: "42px", fontFamily: "Fraunces, serif", fontWeight: 700, color: COLORS.accent }}>
                Originality targets 7+/10
              </div>
              <div style={{ width: "100%", height: "12px", backgroundColor: COLORS.rule, marginTop: "18px", borderRadius: "6px", overflow: "hidden" }}>
                <div style={{ width: "85%", height: "100%", backgroundColor: COLORS.accent }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </SceneContainer>
  );
};

// Scene 3: The Solution (4-Agent Split)
const SolutionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps });

  const card1 = spring({ frame: frame - 30, fps });
  const card2 = spring({ frame: frame - 50, fps });
  const card3 = spring({ frame: frame - 70, fps });
  const card4 = spring({ frame: frame - 90, fps });

  const fade = interpolate(frame, [330, 360], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const agents = [
    { num: "01", name: "Planner", desc: "Builds specification and creative tension.", isIsolated: false },
    { num: "02", name: "Design Agent", desc: "Sees screenshots, writes prose visual design. NEVER sees code.", isIsolated: true },
    { num: "03", name: "Builder", desc: "Faithfully implements prose into HTML/CSS.", isIsolated: false },
    { num: "04", name: "Evaluator", desc: "Interacts in browser, scores visual quality. NEVER sees code.", isIsolated: true },
  ];

  return (
    <SceneContainer>
      <div style={{ opacity: fade, display: "flex", flexDirection: "column", height: "100%", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontFamily: "Space Mono, monospace", fontSize: "24px", color: COLORS.accent, marginBottom: "18px" }}>
            THE METHODOLOGY
          </div>
          <h2
            style={{
              fontFamily: "Fraunces, serif",
              fontSize: "72px",
              fontWeight: 700,
              lineHeight: 1.1,
              margin: 0,
              opacity: titleSpring,
            }}
          >
            Four Isolated Roles. Zero Code-Anchoring.
          </h2>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "30px", margin: "30px 0" }}>
          {agents.map((agent, i) => {
            const cardSpring = [card1, card2, card3, card4][i];
            const scale = interpolate(cardSpring, [0, 1], [0.95, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const y = interpolate(cardSpring, [0, 1], [30, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });

            return (
              <div
                key={i}
                style={{
                  border: `1px solid ${agent.isIsolated ? COLORS.accent : COLORS.rule}`,
                  backgroundColor: COLORS.bg,
                  padding: "36px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  height: "420px",
                  opacity: cardSpring,
                  transform: `translateY(${y}px) scale(${scale})`,
                  position: "relative",
                }}
              >
                {agent.isIsolated && (
                  <span
                    style={{
                      position: "absolute",
                      top: "24px",
                      right: "24px",
                      fontSize: "15px",
                      fontFamily: "Space Mono, monospace",
                      color: COLORS.accent,
                      border: `1px solid ${COLORS.accent}`,
                      padding: "3px 9px",
                      textTransform: "uppercase",
                    }}
                  >
                    Isolated
                  </span>
                )}
                <div style={{ fontFamily: "Space Mono, monospace", fontSize: "24px", color: agent.isIsolated ? COLORS.accent : COLORS.muted }}>
                  {agent.num}
                </div>
                <div>
                  <h3 style={{ fontFamily: "Fraunces, serif", fontSize: "36px", fontWeight: 700, margin: "24px 0 12px 0" }}>
                    {agent.name}
                  </h3>
                  <p style={{ fontSize: "21px", color: COLORS.muted, lineHeight: 1.5, margin: 0 }}>
                    {agent.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ fontSize: "21px", fontFamily: "Space Mono, monospace", color: COLORS.muted, textAlign: "center", opacity: card4 }}>
          * Separated agents communicate only via structured artifacts, not shared state.
        </div>
      </div>
    </SceneContainer>
  );
};

// Scene 4: Scoring Rubric
const ScoringScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps });
  const barSpring = spring({ frame: frame - 40, fps, config: { damping: 15 } });

  const fade = interpolate(frame, [270, 300], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const criteria = [
    { name: "Design Quality", weight: "2x", val: 8 },
    { name: "Originality", weight: "2x", val: 7 },
    { name: "Craftsmanship", weight: "1x", val: 8 },
    { name: "Functionality", weight: "1x", val: 9 },
  ];

  return (
    <SceneContainer>
      <div style={{ opacity: fade, display: "flex", flexDirection: "column", height: "100%", justifyContent: "center" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "90px", alignItems: "center" }}>
          <div>
            <div style={{ fontFamily: "Space Mono, monospace", fontSize: "24px", color: COLORS.accent, marginBottom: "24px" }}>
              THE SCRUTINY
            </div>
            <h2
              style={{
                fontFamily: "Fraunces, serif",
                fontSize: "78px",
                fontWeight: 700,
                lineHeight: 1.1,
                margin: "0 0 30px 0",
                opacity: titleSpring,
              }}
            >
              Strict visual evaluation.
            </h2>
            <p style={{ fontSize: "27px", color: COLORS.muted, lineHeight: 1.6, margin: "0 0 36px 0", opacity: titleSpring }}>
              The evaluator agent opens the page, tests interactivity, and scores across 4 dimensions. Any layout bugs trigger hard score caps.
            </p>
            <div
              style={{
                backgroundColor: COLORS.deep,
                color: COLORS.paper,
                padding: "30px",
                fontFamily: "Space Mono, monospace",
                fontSize: "21px",
                lineHeight: 1.4,
                borderLeft: `3px solid ${COLORS.accent}`,
                opacity: titleSpring,
              }}
            >
              Score = (Design×2 + Orig×2 + Craft + Func) ÷ 6
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "36px" }}>
            {criteria.map((c, i) => {
              const widthVal = interpolate(barSpring, [0, 1], [0, c.val * 10], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });

              return (
                <div key={i} style={{ opacity: barSpring }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", fontSize: "24px", fontWeight: 600 }}>
                    <span>{c.name}</span>
                    <span style={{ color: COLORS.accent, fontFamily: "Space Mono, monospace" }}>
                      {c.weight}
                    </span>
                  </div>
                  <div style={{ width: "100%", height: "36px", border: `1px solid ${COLORS.ink}`, padding: "2px" }}>
                    <div
                      style={{
                        width: `${widthVal}%`,
                        height: "100%",
                        backgroundColor: COLORS.ink,
                        transition: "width 0.1s ease-out",
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </SceneContainer>
  );
};

// Scene 5: CTA Scene
const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps });
  const codeSpring = spring({ frame: frame - 40, fps });

  return (
    <SceneContainer>
      <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "center", alignItems: "center", textAlign: "center" }}>
        <div style={{ fontFamily: "Space Mono, monospace", fontSize: "24px", color: COLORS.accent, marginBottom: "24px" }}>
          GET STARTED
        </div>

        <h2
          style={{
            fontFamily: "Fraunces, serif",
            fontSize: "96px",
            fontWeight: 800,
            lineHeight: 1.1,
            margin: "0 0 36px 0",
            opacity: titleSpring,
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.95, 1])})`,
          }}
        >
          Defeat Template Fatigue.
        </h2>

        <p style={{ fontSize: "30px", color: COLORS.muted, maxWidth: "900px", lineHeight: 1.5, margin: "0 0 60px 0", opacity: titleSpring }}>
          Install the plugin and start generating visual frontends that stand out.
        </p>

        {/* Monospace Command Bar */}
        <div
          style={{
            backgroundColor: COLORS.deep,
            color: COLORS.paper,
            fontFamily: "Space Mono, monospace",
            fontSize: "30px",
            padding: "30px 60px",
            border: `1px solid ${COLORS.rule}`,
            boxShadow: "0 12px 45px rgba(0,0,0,0.15)",
            display: "flex",
            alignItems: "center",
            gap: "24px",
            opacity: codeSpring,
            transform: `translateY(${interpolate(codeSpring, [0, 1], [30, 0])}px)`,
          }}
        >
          <span style={{ color: COLORS.accent }}>›</span>
          <span>claude plugin install https://github.com/George-RD/design-studio</span>
        </div>
      </div>
    </SceneContainer>
  );
};
