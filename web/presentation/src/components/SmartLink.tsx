// Owner: C. Plain anchor for product and NHTSA destinations. Not next/link: the product is a
// different application (outside basePath /observatory), so client-side Next routing must not
// intercept these links.
import type { ReactNode } from "react";
import type { Destination } from "@/content/destinations";

type Props = {
  to: Destination;
  className?: string;
  children: ReactNode;
};

export function SmartLink({ to, className, children }: Props) {
  if (to.external) {
    return (
      <a href={to.href} className={className} target="_blank" rel="noopener noreferrer">
        {children}
        <span className="sr-only"> (opens in a new tab)</span>
      </a>
    );
  }
  return (
    <a href={to.href} className={className}>
      {children}
    </a>
  );
}
