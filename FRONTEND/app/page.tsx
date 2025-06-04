"use client"

import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Brain, Shield, TrendingUp, Users, ArrowRight } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function HomePage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user) {
      router.push("/analyze")
    }
  }, [user, loading, router])











  
  // Initialize particles.js
  useEffect(() => {
    // Load particles.js library
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/particles.js/2.0.0/particles.min.js'
    script.onload = () => {
      // Initialize particles after script loads
      if (window.particlesJS) {
        window.particlesJS('particles-js', {
          particles: {
            number: { value: 120, density: { enable: true, value_area: 800 } },
            color: { value: "#d4d4d8" },
            shape: { type: "circle" },
            opacity: { value: 0.5, random: false },
            size: { value: 3, random: true },
            line_linked: { enable: true, distance: 150, color: "#a1a1aa", opacity: 0.4, width: 1 },
            move: { enable: true, speed: 2, direction: "none", random: false, straight: false, out_mode: "out", bounce: false }
          },
          interactivity: {
            detect_on: "canvas",
            events: { onhover: { enable: true, mode: "repulse" }, onclick: { enable: true, mode: "push" }, resize: true },
            modes: { repulse: { distance: 100, duration: 0.4 }, push: { particles_nb: 4 } }
          },
          retina_detect: true
        })
      }
    }
    document.head.appendChild(script)

    // Cleanup function
    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script)
      }
    }
  }, [])























  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  // return (
  //   <div className="container mx-auto px-4 py-8">
  //     {/* Hero Section */}
  //     <section className="text-center py-20">
  //       <div className="max-w-4xl mx-auto">
  //         <div className="flex justify-center mb-6">
  //           {/* <Brain className="h-16 w-16 text-primary" /> */}
  //            <img src="/image-removebg-preview (5).png" alt="BiaLens Logo" className="h-14 w-50" />
  //         </div>
  //         <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
  //           Detect Bias with AI
  //         </h1>
  //         <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto">
  //           BiaLens uses advanced AI to analyze text for bias, sentiment, and misinformation. Build trust in information
  //           with transparent, real-time analysis.
  //         </p>
  //         <div className="flex flex-col sm:flex-row gap-4 justify-center">
  //           <Link href="/auth/signup">
  //             <Button size="lg" className="text-lg px-8 py-6">
  //               Get Started Free
  //               <ArrowRight className="ml-2 h-5 w-5" />
  //             </Button>
  //           </Link>
  //           <Link href="/auth/signin">
  //             <Button variant="outline" size="lg" className="text-lg px-8 py-6">
  //               Sign In
  //             </Button>
  //           </Link>
  //         </div>
  //       </div>
  //     </section>

  //     {/* Features Section */}
  //     <section className="py-20">
  //       <div className="max-w-6xl mx-auto">
  //         <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">Why Choose BiaLens?</h2>
  //         <div className="grid md:grid-cols-3 gap-8">
  //           <Card className="text-center p-6">
  //             <CardContent className="pt-6">
  //               <Shield className="h-12 w-12 text-primary mx-auto mb-4" />
  //               <h3 className="text-xl font-semibold mb-3">Multi-Layer Detection</h3>
  //               <p className="text-muted-foreground">
  //                 Advanced AI combines sentiment analysis, bias detection, and misinformation flagging in one
  //                 comprehensive tool.
  //               </p>
  //             </CardContent>
  //           </Card>

  //           <Card className="text-center p-6">
  //             <CardContent className="pt-6">
  //               <TrendingUp className="h-12 w-12 text-primary mx-auto mb-4" />
  //               <h3 className="text-xl font-semibold mb-3">Trust Score</h3>
  //               <p className="text-muted-foreground">
  //                 Get an instant 0-100% trust score with detailed explanations for every analysis result.
  //               </p>
  //             </CardContent>
  //           </Card>

  //           <Card className="text-center p-6">
  //             <CardContent className="pt-6">
  //               <Users className="h-12 w-12 text-primary mx-auto mb-4" />
  //               <h3 className="text-xl font-semibold mb-3">Built for Gen Z</h3>
  //               <p className="text-muted-foreground">
  //                 Designed specifically for students, researchers, and young professionals who need reliable
  //                 information.
  //               </p>
  //             </CardContent>
  //           </Card>
  //         </div>
  //       </div>
  //     </section>

  //     {/* How It Works */}
  //     <section className="py-20 bg-muted/50 rounded-lg">
  //       <div className="max-w-4xl mx-auto px-6">
  //         <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">How It Works</h2>
  //         <div className="space-y-8">
  //           <div className="flex items-start gap-4">
  //             <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
  //               1
  //             </div>
  //             <div>
  //               <h3 className="text-xl font-semibold mb-2">Paste Your Text</h3>
  //               <p className="text-muted-foreground">
  //                 Copy and paste any article, social media post, or news content into our analyzer.
  //               </p>
  //             </div>
  //           </div>

  //           <div className="flex items-start gap-4">
  //             <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
  //               2
  //             </div>
  //             <div>
  //               <h3 className="text-xl font-semibold mb-2">AI Analysis</h3>
  //               <p className="text-muted-foreground">
  //                 Our AI examines the text for emotional language, bias patterns, and potential misinformation.
  //               </p>
  //             </div>
  //           </div>

  //           <div className="flex items-start gap-4">
  //             <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold">
  //               3
  //             </div>
  //             <div>
  //               <h3 className="text-xl font-semibold mb-2">Get Insights</h3>
  //               <p className="text-muted-foreground">
  //                 Receive a detailed report with trust score, bias flags, and clear explanations.
  //               </p>
  //             </div>
  //           </div>
  //         </div>
  //       </div>
  //     </section>

  //     {/* CTA Section */}
  //     <section className="py-20 text-center">
  //       <div className="max-w-3xl mx-auto">
  //         <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to Analyze Your First Text?</h2>
  //         <p className="text-xl text-muted-foreground mb-8">
  //           Join thousands of users who trust BiaLens for reliable information analysis.
  //         </p>
  //         <Link href="/auth/signup">
  //           <Button size="lg" className="text-lg px-8 py-6">
  //             Start Analyzing Now
  //             <ArrowRight className="ml-2 h-5 w-5" />
  //           </Button>
  //         </Link>
  //       </div>
  //     </section>
  //   </div>
  // )

  return (
    <div>
      {/* Hero Section */}
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-5xl w-full bg-white backdrop-blur-lg rounded-2xl overflow-hidden beautiful-shadow border border-neutral-200 flex flex-col lg:flex-row">
          {/* Particles Visualization Column */}
          <div className="lg:w-3/5 h-96 lg:h-auto relative bg-gradient-to-br from-green-900 to-green-700" id="particles-container">
            <div id="particles-js"></div>
            <div className="absolute inset-0 flex flex-col justify-center items-start p-8 lg:p-12 z-10">
              <span className="px-4 py-2 bg-green-700/80 rounded-full text-sm text-neutral-200 mb-6">FIGHT THE FAKE</span>
              <h1 className="heading-font text-4xl lg:text-6xl text-white mb-4 leading-tight font-black">
                Detect bias.<br />
                Unmask clickbait.<br />
                <span className="accent-green">Trust your news.</span>
              </h1>
              <p className="text-neutral-100 text-lg mb-8 max-w-md">
                BiasLens instantly analyzes news headlines, tweets, and forwards for suggestive language, political slant, and AI-generated or misleading content.<br />
                <span className="accent-green font-bold">Stay sharp.</span>
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <button className="px-8 py-4 bg-white text-green-700 rounded-lg heading-font text-sm hover:bg-green-50 transition flex items-center justify-center font-bold">
                  Analyze Text
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
                <button className="px-8 py-4 border border-green-100 text-neutral-100 rounded-lg heading-font text-sm hover:bg-green-800 transition font-semibold">
                  Watch Demo
                </button>
              </div>
            </div>
            <div className="absolute bottom-6 right-6 bg-green-800/80 backdrop-blur-sm rounded-lg px-4 py-3 z-10 border border-green-700">
              <div className="text-xs text-green-200 mb-1">News Analyzed Today</div>
              <div className="heading-font text-2xl text-green-100 font-bold">6,301</div>
            </div>
          </div>

          {/* Content Column */}
          <div className="lg:w-2/5 p-8 lg:p-12 bg-white flex flex-col justify-center">
            <div className="mb-8">
              <span className="px-3 py-1 bg-green-50 rounded-full text-xs text-green-700 mb-4 inline-block font-semibold">WHY BIASLENS?</span>
              <h2 className="heading-font text-3xl text-neutral-800 mb-4 font-bold">Trust what you read</h2>
              <p className="text-neutral-600 mb-6">BiasLens is built for the modern reader, student, and activist—helping you spot media manipulation, emotional slant, and false claims in seconds.</p>
            </div>

            <div className="space-y-6">
              <div className="flex items-start">
                <div className="w-8 h-8 bg-green-700 rounded-lg flex items-center justify-center mr-4 mt-1">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="heading-font text-lg text-neutral-800 mb-1 font-semibold">Instant Feedback</h3>
                  <p className="text-neutral-600 text-sm">Paste any headline, tweet, or WhatsApp forward and get a bias report instantly.</p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-8 h-8 bg-green-700 rounded-lg flex items-center justify-center mr-4 mt-1">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <div>
                  <h3 className="heading-font text-lg text-neutral-800 mb-1 font-semibold">Private & Secure</h3>
                  <p className="text-neutral-600 text-sm">No logs. No tracking. Your submissions stay private and secure.</p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-8 h-8 bg-green-700 rounded-lg flex items-center justify-center mr-4 mt-1">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="heading-font text-lg text-neutral-800 mb-1 font-semibold">Unbiased AI</h3>
                  <p className="text-neutral-600 text-sm">BiasLens is trained on diverse sources—fighting misinformation for all communities.</p>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-neutral-200">
              <p className="text-xs text-green-800 mb-3">Trusted by students & journalists at</p>
              <div className="flex items-center space-x-4 text-green-500">
                <span className="text-sm font-medium">Unilag</span>
                <span className="text-sm font-medium">Covenant</span>
                <span className="text-sm font-medium">ChannelsTV</span>
                <span className="text-sm font-medium">TheCable</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Replace script tag with useEffect for particlesJS */}
      <section className="max-w-6xl mx-auto py-20 px-4">
        <span className="px-3 py-1 bg-green-50 rounded-full text-xs text-green-700 mb-5 inline-block font-semibold">WHY CHOOSE BIASLENS?</span>
        <h2 className="heading-font text-3xl md:text-4xl text-neutral-900 font-bold mb-8">Why Choose BiasLens?</h2>
        <div className="grid gap-10 md:grid-cols-3">
          <div className="bg-white rounded-xl p-7 shadow border border-green-50 flex flex-col items-start">
            <div className="bg-green-700 text-white rounded-lg p-3 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405M19 13V7a2 2 0 00-2-2H7.825a1 1 0 00-.707.293l-4.825 4.825a2.002 2.002 0 000 2.83l6 6A2.003 2.003 0 0011 21h8a1 1 0 001-1v-6a1 1 0 00-1-1z" />
              </svg>
            </div>
            <h3 className="heading-font text-xl text-neutral-800 font-semibold mb-2">Multi-Layer Detection</h3>
            <p className="text-neutral-600">Advanced AI combines sentiment analysis, bias detection, and misinformation flagging in one comprehensive tool.</p>
          </div>
          <div className="bg-white rounded-xl p-7 shadow border border-green-50 flex flex-col items-start">
            <div className="bg-green-700 text-white rounded-lg p-3 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 1.343-3 3a3 3 0 006 0c0-1.657-1.343-3-3-3zm0 14s-8-4-8-10a8 8 0 1116 0c0 6-8 10-8 10z" />
              </svg>
            </div>
            <h3 className="heading-font text-xl text-neutral-800 font-semibold mb-2">Trust Score</h3>
            <p className="text-neutral-600">Get an instant 0-100% trust score with detailed explanations for every analysis result.</p>
          </div>
          <div className="bg-white rounded-xl p-7 shadow border border-green-50 flex flex-col items-start">
            <div className="bg-green-700 text-white rounded-lg p-3 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m4 0h1m-2-6h.01M8 12v.01M2 12a10 10 0 1020 0 10 10 0 00-20 0z" />
              </svg>
            </div>
            <h3 className="heading-font text-xl text-neutral-800 font-semibold mb-2">Built for Gen Z</h3>
            <p className="text-neutral-600">Designed specifically for students, researchers, and young professionals who need reliable information.</p>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-gradient-to-bl from-green-50 to-white py-20 mt-12">
        <div className="max-w-5xl mx-auto px-4">
          <span className="px-3 py-1 bg-green-50 rounded-full text-xs text-green-700 mb-5 inline-block font-semibold">HOW IT WORKS</span>
          <h2 className="heading-font text-3xl md:text-4xl text-neutral-900 font-bold mb-8">How It Works</h2>
          <div className="grid gap-12 md:grid-cols-3">
            {/* Step 1 */}
            <div className="flex flex-col items-center text-center">
              <div className="bg-green-600 text-white rounded-full h-12 w-12 flex items-center justify-center mb-3 text-xl font-bold shadow">1</div>
              <h3 className="heading-font text-lg font-semibold mb-2 text-neutral-800">Paste Your Text</h3>
              <p className="text-neutral-600">Copy and paste any article, social media post, or news content into our analyzer.</p>
            </div>
            {/* Step 2 */}
            <div className="flex flex-col items-center text-center">
              <div className="bg-green-600 text-white rounded-full h-12 w-12 flex items-center justify-center mb-3 text-xl font-bold shadow">2</div>
              <h3 className="heading-font text-lg font-semibold mb-2 text-neutral-800">AI Analysis</h3>
              <p className="text-neutral-600">Our AI examines the text for emotional language, bias patterns, and potential misinformation.</p>
            </div>
            {/* Step 3 */}
            <div className="flex flex-col items-center text-center">
              <div className="bg-green-600 text-white rounded-full h-12 w-12 flex items-center justify-center mb-3 text-xl font-bold shadow">3</div>
              <h3 className="heading-font text-lg font-semibold mb-2 text-neutral-800">Get Insights</h3>
              <p className="text-neutral-600">Receive a detailed report with trust score, bias flags, and clear explanations.</p>
            </div>
          </div>
        </div>
      </section>

      {/* READY TO ANALYZE - CALL TO ACTION */}
      <section className="py-16 max-w-4xl mx-auto flex flex-col items-center gap-6 text-center px-4">
        <h2 className="heading-font text-3xl md:text-4xl text-neutral-900 font-bold mb-6">Ready to Analyze Your First Text?</h2>
        <p className="text-lg text-neutral-700 mb-6">Join thousands of users who trust <span className="accent-green font-bold">BiasLens</span> for reliable information analysis.</p>
        <button className="px-8 py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl heading-font text-lg font-semibold shadow transition">
          Start Analyzing Now
        </button>
      </section>

      {/* FOOTER */}
      <footer className="bg-neutral-950 text-neutral-200 py-12 mt-10">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:justify-between gap-10 md:gap-0 px-4">
          <div>
            <div className="flex items-center mb-3">
              <span className="px-2 py-1 rounded-full bg-green-500 text-white text-sm font-semibold">BiasLens</span>
              <span className="ml-3 heading-font font-bold text-lg text-white">Trust Your News</span>
            </div>
            <p className="max-w-xs text-neutral-400">AI-powered bias analysis. Built for students, journalists, and anyone who wants the truth.</p>
          </div>
          <div>
            <h4 className="font-bold text-neutral-100 mb-2">Product</h4>
            <ul className="space-y-1 text-neutral-400">
              <li><a href="#" className="hover:text-green-400 transition">How it Works</a></li>
              <li><a href="#" className="hover:text-green-400 transition">Features</a></li>
              <li><a href="#" className="hover:text-green-400 transition">Pricing</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-neutral-100 mb-2">Company</h4>
            <ul className="space-y-1 text-neutral-400">
              <li><a href="#" className="hover:text-green-400 transition">About</a></li>
              <li><a href="#" className="hover:text-green-400 transition">Contact</a></li>
              <li><a href="#" className="hover:text-green-400 transition">Blog</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-neutral-100 mb-2">Legal</h4>
            <ul className="space-y-1 text-neutral-400">
              <li><a href="#" className="hover:text-green-400 transition">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-green-400 transition">Terms of Service</a></li>
            </ul>
          </div>
        </div>
        <div className="text-center text-neutral-500 text-xs mt-10">
          &copy; 2024 BiasLens. All rights reserved.
        </div>
      </footer>
    </div>
  )
}