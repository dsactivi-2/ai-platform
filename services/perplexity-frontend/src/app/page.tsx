"use client";

import { ChatPanel } from "@/components/chat-panel";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { USER_KEY } from "@/lib/constants";
import { Suspense, useEffect, useState } from "react";

const LoginPrompt = () => {
  const handleLogin = () => {
    // Remove any query parameters and refresh the page
    const currentUrl = new URL(window.location.href);
    const cleanUrl = `${currentUrl.origin}${currentUrl.pathname}`;
    window.location.href = cleanUrl;
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-full p-4 md:p-6 lg:p-8">
      <div className="w-full max-w-(--breakpoint-md) text-center space-y-6">
        <div className="space-y-4">
          <h1 className="text-3xl md:text-4xl font-bold text-foreground">
            Welcome to Perplexity OSS
          </h1>
          <p className="text-base text-muted-foreground leading-relaxed">
            Please authenticate with your Lyzr account to continue exploring our AI-powered search engine
          </p>
        </div>
        <Button onClick={handleLogin} size="lg" className="w-full sm:w-auto">
          Login with Lyzr
        </Button>
      </div>
    </div>
  );
};

export default function Home() {
  // Auth bypassed - Gateway Basic Auth handles access control
  return (
    <div className="flex grow h-full mx-auto w-full max-w-(--breakpoint-md) duration-200 px-4 md:px-8">
      <Suspense fallback={
        <div className="flex items-center justify-center w-full">
          <div className="text-center space-y-4">
            <div className="w-8 h-8 bg-primary/20 rounded-full mx-auto flex items-center justify-center animate-pulse">
              <div className="w-4 h-4 bg-primary rounded-full animate-ping"></div>
            </div>
            <p className="text-sm text-muted-foreground">Loading chat...</p>
          </div>
        </div>
      }>
        <ChatPanel />
      </Suspense>
    </div>
  );
}
